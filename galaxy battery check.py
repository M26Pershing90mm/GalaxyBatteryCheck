"""Samsung Galaxy battery diagnostics over ADB (read-only, no root required).

Requires Android SDK Platform-Tools (adb) and USB debugging authorization.
Only reports values actually exposed by the connected device.
"""

from __future__ import annotations

import argparse
import ctypes
import runpy
import json
import math
import shutil
import tempfile
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any


APP_NAME = "Galaxy Battery Check"
APP_VERSION = "1.4.4"
APP_AUTHOR = "Sakai"
COPYRIGHT_HOLDER = "꿈을꾸는 파랑새"
BLOG_URL = "https://wezard4u.tistory.com/"
DONATION_URL = "https://toon.at/donate/637833976686140024"
KOFI_URL = "https://ko-fi.com/sakai38666"
COPYRIGHT_NOTICE = f"© 2026 {COPYRIGHT_HOLDER}. All rights reserved."
AUTHOR_NOTICE = f"Developed by {APP_AUTHOR} | {COPYRIGHT_NOTICE}"


def language_from_tag(tag: str | None) -> str:
    lang = (tag or "").replace("_", "-").lower().split("-")[0]
    return lang if lang in {"ko", "en", "ja"} else "en"


def windows_display_language() -> str:
    if sys.platform != "win32":
        return "en"
    try:
        kernel32 = ctypes.windll.kernel32
        preferred = getattr(kernel32, "GetUserPreferredUILanguages", None)
        if preferred is not None:
            language_count = ctypes.c_ulong(0)
            buffer_length = ctypes.c_ulong(0)
            flags = 0x00000008
            if preferred(flags, ctypes.byref(language_count), None, ctypes.byref(buffer_length)) and buffer_length.value:
                buffer = ctypes.create_unicode_buffer(buffer_length.value)
                if preferred(flags, ctypes.byref(language_count), buffer, ctypes.byref(buffer_length)):
                    language_tag = buffer.value.strip()
                    if language_tag:
                        return language_from_tag(language_tag)
        langid = kernel32.GetUserDefaultUILanguage()
        primary = int(langid) & 0x3FF
        return {0x12: "ko", 0x09: "en", 0x11: "ja"}.get(primary, "en")
    except (AttributeError, OSError, ValueError, TypeError):
        return "en"


def donation_url(language: str | None = None) -> str:
    code = language if language in {"ko", "en", "ja"} else windows_display_language()
    return DONATION_URL if code == "ko" else KOFI_URL


class AdbError(RuntimeError):
    """A categorised ADB failure with language-neutral information for the UI."""

    def __init__(self, message: str, code: str = "adb_failed", **details: str) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


ADB_ERROR_MESSAGES = {
    "ko": {
        "invalid_executable": "ADB 실행 파일을 확인할 수 없습니다. 공식 Android SDK Platform-Tools의 adb.exe를 선택하세요.",
        "missing_executable": "adb.exe를 찾지 못했습니다. Platform-Tools를 설치하거나 올바른 경로를 선택하세요.",
        "timeout": "ADB 응답 시간이 초과되었습니다. 연결 상태를 확인한 후 다시 시도하세요.",
        "output_too_large": "ADB 응답 크기가 제한을 초과했습니다. 연결된 기기 및 ADB 상태를 확인하세요.",
        "command_failed": "ADB 명령 실행에 실패했습니다. USB 디버깅 승인 및 기기 연결을 확인하세요.",
        "device_not_listed": "선택한 기기를 ADB 목록에서 찾지 못했습니다. 기기를 다시 검색하세요.",
        "device_not_ready": "선택한 기기를 사용할 수 없습니다. USB 디버깅 승인 및 연결 상태를 확인하세요.",
        "multiple_devices": "여러 기기가 연결되어 있습니다. 사용할 기기를 선택하세요.",
        "no_ready_device": "연결된 기기가 준비되지 않았습니다. USB 디버깅 승인 상태를 확인하세요.",
        "no_device": "연결된 Android 기기가 없습니다. USB 케이블 및 디버깅 설정을 확인하세요.",
        "invalid_battery_data": "배터리 정보가 정상적으로 반환되지 않았습니다.",
        "adb_failed": "ADB 작업에 실패했습니다. 실행 파일과 기기 연결을 확인하세요.",
    },
    "en": {
        "invalid_executable": "The ADB executable is invalid. Select adb.exe from the official Android SDK Platform-Tools.",
        "missing_executable": "adb.exe was not found. Install Platform-Tools or select the correct file.",
        "timeout": "ADB timed out. Check the device connection and try again.",
        "output_too_large": "The ADB response exceeded the size limit. Check the connected device and ADB status.",
        "command_failed": "The ADB command failed. Check the USB debugging authorization and device connection.",
        "device_not_listed": "The selected device is not listed by ADB. Scan for devices again.",
        "device_not_ready": "The selected device is not ready. Check USB debugging authorization and the connection.",
        "multiple_devices": "Multiple devices are connected. Select the device to use.",
        "no_ready_device": "No connected device is ready. Check USB debugging authorization.",
        "no_device": "No Android device is connected. Check the USB cable and debugging settings.",
        "invalid_battery_data": "The device did not return valid battery information.",
        "adb_failed": "The ADB operation failed. Check the executable and device connection.",
    },
    "ja": {
        "invalid_executable": "ADB実行ファイルを確認できません。公式Android SDK Platform-Toolsのadb.exeを選択してください。",
        "missing_executable": "adb.exeが見つかりません。Platform-Toolsを導入するか、正しいファイルを選択してください。",
        "timeout": "ADBの応答がタイムアウトしました。接続を確認して再試行してください。",
        "output_too_large": "ADBの応答がサイズ制限を超えました。端末とADBの状態を確認してください。",
        "command_failed": "ADBコマンドの実行に失敗しました。USBデバッグの許可と接続を確認してください。",
        "device_not_listed": "選択した端末がADBの一覧にありません。端末を再検索してください。",
        "device_not_ready": "選択した端末を使用できません。USBデバッグの許可と接続を確認してください。",
        "multiple_devices": "複数の端末が接続されています。使用する端末を選択してください。",
        "no_ready_device": "使用可能な端末がありません。USBデバッグの許可を確認してください。",
        "no_device": "Android端末が接続されていません。USBケーブルとデバッグ設定を確認してください。",
        "invalid_battery_data": "端末から正常なバッテリー情報が返されませんでした。",
        "adb_failed": "ADBの処理に失敗しました。実行ファイルと接続を確認してください。",
    },
}


def localized_adb_error(error: AdbError, language: str = "en") -> str:
    """Translate known errors without displaying untrusted device output in the GUI."""
    translations = ADB_ERROR_MESSAGES[language_from_tag(language)]
    return translations.get(error.code, translations["adb_failed"])


MAX_ADB_STDOUT = 2 * 1024 * 1024
MAX_ADB_STDERR = 256 * 1024


def adb_call(adb: str, args: list[str], timeout: int = 12, optional: bool = False) -> str | None:
    """Run an ADB subprocess without a shell or unbounded RAM output buffers."""
    if sys.platform == "win32":
        resolved = shutil.which(adb)
        if not resolved or Path(resolved).name.casefold() != "adb.exe":
            raise AdbError("Windows에서는 공식 Platform-Tools의 adb.exe 실행 파일만 지정하세요.", code="invalid_executable")
        adb = str(Path(resolved).resolve())
    try:
        with tempfile.TemporaryFile(mode="w+b") as output, tempfile.TemporaryFile(mode="w+b") as errors:
            completed = subprocess.run(
                [adb, *args],
                stdout=output,
                stderr=errors,
                timeout=timeout,
                check=False,
                shell=False,
                # adb.exe is a console program. Hide its transient console on Windows.
                creationflags=(getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                               if sys.platform == "win32" else 0),
            )
            if completed.returncode != 0 and optional:
                return None
            output.seek(0, 2)
            errors.seek(0, 2)
            if output.tell() > MAX_ADB_STDOUT or errors.tell() > MAX_ADB_STDERR:
                if optional:
                    return None
                raise AdbError("ADB 응답이 허용된 크기를 초과했습니다.", code="output_too_large")
            output.seek(0)
            errors.seek(0)
            stdout = output.read().decode("utf-8", errors="replace").strip()
            stderr = errors.read().decode("utf-8", errors="replace").strip()
            if completed.returncode != 0:
                raise AdbError(f"ADB 오류: {stderr or stdout or '원인 불명 오류'}", code="command_failed")
            return stdout
    except FileNotFoundError as exc:
        raise AdbError("adb 실행 파일을 찾지 못했습니다. Android SDK Platform-Tools를 설치하거나 --adb 경로를 지정하세요.", code="missing_executable") from exc
    except subprocess.TimeoutExpired as exc:
        if optional:
            return None
        raise AdbError(f"ADB 응답 시간 초과: {' '.join(args)}", code="timeout") from exc


def select_device(adb: str, serial: str | None) -> str:
    output = adb_call(adb, ["devices", "-l"])
    assert output is not None
    devices: dict[str, str] = {}
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            devices[parts[0]] = parts[1]

    if serial is not None:
        if serial not in devices:
            raise AdbError(f"지정한 기기({serial})가 ADB 목록에 없습니다. adb devices -l 명령으로 확인하세요.", code="device_not_listed")
        if devices[serial] != "device":
            raise AdbError(f"기기 {serial} 상태가 '{devices[serial]}'입니다. 스마트폰에서 USB 디버깅을 허용하세요.", code="device_not_ready")
        return serial

    connected = [key for key, state in devices.items() if state == "device"]
    if len(connected) == 1:
        return connected[0]
    if len(connected) > 1:
        raise AdbError("기기가 여러 대 연결되어 있습니다. --serial SERIAL 옵션으로 하나를 선택하세요.", code="multiple_devices")
    if devices:
        states = ", ".join(f"{key}={state}" for key, state in devices.items())
        raise AdbError(f"사용 가능한 기기가 없습니다({states}). USB 디버깅 승인 여부를 확인하세요.", code="no_ready_device")
    raise AdbError("연결된 Android 기기가 없습니다. USB 케이블과 디버깅 설정을 확인하세요.", code="no_device")


def number_from_field(text: str, field: str) -> float | None:
    """Read a whole-line `field: 98.710` or `field: [99]` value."""
    pattern = rf"(?mi)^\s*{re.escape(field)}\s*:\s*\[?\s*(-?\d+(?:\.\d+)?)"
    match = re.search(pattern, text)
    if not match or len(match.group(1)) > 64:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def percentage(text: str, field: str) -> float | None:
    value = number_from_field(text, field)
    return value if value is not None and 0 < value <= 100 else None


def parse_first_use(text: str) -> str | None:
    pattern = r"(?mi)^\s*(?:battery FirstUseDate|mSavedBatteryFirstUseDate)\s*:\s*\[?\s*(\d{8})\b"
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_dump(text: str) -> dict[str, Any]:
    bsoh = percentage(text, "mSavedBatteryBsoh")
    asoc = percentage(text, "mSavedBatteryAsoc")
    level = number_from_field(text, "level")
    temperature = number_from_field(text, "temperature")
    max_temp = number_from_field(text, "mSavedBatteryMaxTemp")
    charge_counter = number_from_field(text, "charge counter")
    usage_raw = number_from_field(text, "mSavedBatteryUsage")

    native_cycle = None
    for field in ("cycle count", "cycle_count", "cycleCount"):
        native_cycle = number_from_field(text, field)
        if native_cycle is not None and native_cycle >= 0:
            break

    result: dict[str, Any] = {
        "bsoh_pct": bsoh,
        "asoc_pct": asoc,
        "asoc_source": "Samsung dumpsys" if asoc is not None else None,
        "level_pct": int(level) if level is not None and 0 <= level <= 100 else None,
        "temperature_c": round(temperature / 10, 1) if temperature is not None and -400 <= temperature <= 1000 else None,
        "max_temperature_c": round(max_temp / 10, 1) if max_temp is not None and 0 <= max_temp <= 1000 else None,
        "first_use_date": parse_first_use(text),
        "charge_counter_mah": round(charge_counter / 1000, 2) if charge_counter is not None and charge_counter >= 0 else None,
        "usage_raw": int(usage_raw) if usage_raw is not None and usage_raw >= 0 else None,
        "cycle_count": None,
        "cycle_source": None,
    }
    if native_cycle is not None and native_cycle >= 0:
        result["cycle_count"] = int(native_cycle)
        result["cycle_source"] = "Android dumpsys"
    return result


def read_sysfs(adb: str, serial: str, filename: str) -> float | None:
    """Read only a known, immutable sysfs path; permission errors mean unavailable."""
    if filename not in {"cycle_count", "battery_cycle", "fg_asoc", "charge_full", "charge_full_design"}:
        raise ValueError("허용되지 않은 sysfs 항목")
    path = f"/sys/class/power_supply/battery/{filename}"
    output = adb_call(adb, ["-s", serial, "shell", "cat", path], optional=True)
    if output is None:
        return None
    match = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*", output)
    if not match or len(match.group(1)) > 64:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def mah_from_sysfs(value: float | None) -> float | None:
    """Often reported as uAh, but some vendors use mAh; only accept plausible values."""
    if value is None or value <= 0:
        return None
    mah = value / 1000 if value > 100000 else value
    return round(mah, 2) if 100 <= mah <= 30000 else None


def collect(adb: str, serial: str, rated_mah: float | None, skip_sysfs: bool) -> dict[str, Any]:
    prefix = ["-s", serial, "shell"]
    raw = adb_call(adb, [*prefix, "dumpsys", "battery"], timeout=20)
    assert raw is not None
    if not raw or "level" not in raw.lower():
        raise AdbError("배터리 데이터가 정상적으로 반환되지 않았습니다.", code="invalid_battery_data")

    battery = parse_dump(raw)

    if not skip_sysfs:
        if battery["asoc_pct"] is None:
            asoc_sysfs = read_sysfs(adb, serial, "fg_asoc")
            if asoc_sysfs is not None and 0 < asoc_sysfs <= 100:
                battery["asoc_pct"] = asoc_sysfs
                battery["asoc_source"] = "sysfs fg_asoc (보조값)"

        if battery["cycle_count"] is None:
            for name in ("cycle_count", "battery_cycle"):
                cycles = read_sysfs(adb, serial, name)
                if cycles is not None and 0 < cycles <= 100000:
                    battery["cycle_count"] = int(cycles)
                    battery["cycle_source"] = f"sysfs {name}"
                    break

    if battery["cycle_count"] is None and battery["usage_raw"] is not None:
        battery["cycle_count"] = round(battery["usage_raw"] / 100.0, 2)
        battery["cycle_source"] = "Samsung 누적 사용량 환산 추정치"

    level = battery["level_pct"]
    remain = battery["charge_counter_mah"]
    battery["extrapolated_full_mah"] = (
        round(remain / (level / 100), 1)
        if remain is not None and level is not None and 20 <= level <= 100 and remain > 0
        else None
    )
    battery["rated_capacity_mah"] = rated_mah
    battery["extrapolated_to_rated_pct"] = (
        round(battery["extrapolated_full_mah"] / rated_mah * 100, 1)
        if rated_mah and battery["extrapolated_full_mah"] is not None
        else None
    )

    return {
        "application": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "author": APP_AUTHOR,
            "copyright": COPYRIGHT_NOTICE,
            "blog_url": BLOG_URL,
            "donation_url": donation_url(),
        },
        "device": {
            "serial": serial,
            "manufacturer": adb_call(adb, [*prefix, "getprop", "ro.product.manufacturer"], optional=True),
            "model": adb_call(adb, [*prefix, "getprop", "ro.product.model"], optional=True),
            "android_version": adb_call(adb, [*prefix, "getprop", "ro.build.version.release"], optional=True),
        },
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "battery": battery,
    }


def report_for_export(report: dict[str, Any], include_serial: bool = False) -> dict[str, Any]:
    """Privacy-safe JSON export without mutating the original diagnostic data."""
    if include_serial:
        return report
    return {
        **report,
        "device": {**report["device"], "serial": "REDACTED"},
    }


CLI_TEXT = {
    "ko": {
        "error_prefix": "오류", "rated_error": "--rated-mah는 100~30000 범위의 mAh 값이어야 합니다.",
        "browser_open": "브라우저로 열기: {url}",
        "browser_failed": "브라우저를 자동으로 열지 못했습니다. 직접 열어주세요: {url}",
        "saved": "JSON 파일 저장: {path}",
        "warnings": (
            "비공식 독립 개발 도구이며 삼성전자에서 승인·인증한 프로그램이 아닙니다.",
            "BSOH/ASOC는 기기 보고값이며 정밀 실측치가 아닙니다.",
            "충전량 역산은 참고용으로, BSOH/ASOC 대체값이 아닙니다.",
            "최고 온도와 최초 사용일의 기록 범위는 보장되지 않습니다.",
            "표시되지 않는 필드는 지원하지 않거나 읽기 권한이 없을 수 있습니다.",
        ),
    },
    "en": {
        "error_prefix": "Error", "rated_error": "--rated-mah must be between 100 and 30000 mAh.",
        "browser_open": "Opening in browser: {url}",
        "browser_failed": "Could not open the browser automatically. Open this URL manually: {url}",
        "saved": "JSON report saved: {path}",
        "warnings": (
            "This is independent, unofficial software; it is not approved or certified by Samsung Electronics.",
            "BSOH/ASOC values are reported by the device, not measured in a laboratory.",
            "Extrapolated charge capacity is for reference only and does not replace BSOH/ASOC.",
            "The coverage of the maximum-temperature and first-use records is not guaranteed.",
            "Unavailable fields may not be supported or accessible on this device.",
        ),
    },
    "ja": {
        "error_prefix": "エラー", "rated_error": "--rated-mahには100～30000 mAhの値を指定してください。",
        "browser_open": "ブラウザーで開く: {url}",
        "browser_failed": "ブラウザーを自動的に開けません。手動で開いてください: {url}",
        "saved": "JSONファイルを保存しました: {path}",
        "warnings": (
            "本ソフトは非公式の個人開発ツールであり、Samsung Electronicsの承認・認定を受けていません。",
            "BSOH/ASOCは端末が報告した値で、精密測定値ではありません。",
            "充電量からの容量推定は参考値であり、BSOH/ASOCの代替値ではありません。",
            "最高温度と初回使用日の記録範囲は保証されません。",
            "表示できない項目は、端末が非対応または読み取り権限がない場合があります。",
        ),
    },
}


def display(report: dict[str, Any], language: str = "ko") -> None:
    device = report["device"]
    battery = report["battery"]

    def fmt(key: str, unit: str = "", places: int = 1) -> str:
        value = battery[key]
        if value is None:
            return "확인 불가"
        if isinstance(value, float):
            return f"{value:.{places}f}{unit}"
        return f"{value}{unit}"

    print("=" * 52)
    print(" Galaxy Battery Check (Unofficial)  |  ADB / Read-only")
    print("=" * 52)
    print(f"모델: {device['model'] or '확인 불가'}")
    print(f"Android: {device['android_version'] or '확인 불가'}")
    print(f"측정 시각: {report['checked_at']}")
    print("-" * 52)
    print(f"BSOH (우선 지표)  : {fmt('bsoh_pct', '%', 2)}")
    print(f"ASOC (보조 지표)  : {fmt('asoc_pct', '%', 2)}"
          + (f" [{battery['asoc_source']}]" if battery['asoc_source'] else ""))
    print(f"배터리 잔량       : {fmt('level_pct', '%')}")
    print(f"현재 온도         : {fmt('temperature_c', '°C')}")
    print(f"기록된 최고 온도  : {fmt('max_temperature_c', '°C')}")
    print(f"최초 사용 기록일  : {fmt('first_use_date')}")
    print(f"충전 사이클       : {fmt('cycle_count', '회', 2)}"
          + (f" [{battery['cycle_source']}]" if battery['cycle_source'] else ""))
    print(f"누적 사용량 원문  : {fmt('usage_raw')}")
    print(f"현재 잔여 전하량  : {fmt('charge_counter_mah', ' mAh', 2)}")
    print(f"완충 용량 간이 추정: {fmt('extrapolated_full_mah', ' mAh')}")
    if battery["rated_capacity_mah"] is not None:
        print(f"정격 용량 대비 추정: {fmt('extrapolated_to_rated_pct', '%')}")
    print("-" * 52)
    for warning in CLI_TEXT[language_from_tag(language)]["warnings"]:
        print(f"※ {warning}")
    print(f"블로그: {BLOG_URL}")
    print(f"후원 페이지: {report['application']['donation_url']}")


def main() -> int:
    if len(sys.argv) == 1:
        gui_file = Path(__file__).with_name("galaxy battery gui.py")
        if gui_file.is_file():
            runpy.run_path(str(gui_file), run_name="__main__")
            return 0
    parser = argparse.ArgumentParser(
        description="갤럭시 배터리 지표를 ADB로 읽는 비공식 Python 도구 (읽기 전용)",
        epilog=AUTHOR_NOTICE,
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} (Unofficial) v{APP_VERSION} | {AUTHOR_NOTICE}")
    parser.add_argument("--donate", action="store_true", help="Windows 언어에 맞는 후원 페이지 열기")
    parser.add_argument("--language", choices=["ko", "en", "ja"], help="후원 URL용 언어 선택 (기본: Windows 표시 언어)")
    parser.add_argument("--blog", action="store_true", help="기본 브라우저로 개발자 블로그 열기")
    parser.add_argument("--adb", default="adb", help="adb 실행 파일 경로 또는 명령어 (기본값: adb)")
    parser.add_argument("--serial", help="ADB 기기 시리얼 (2대 이상 연결된 경우 필요)")
    parser.add_argument("--rated-mah", type=float, help="기기 사양의 정격 용량(mAh), 간이 추정치 비교에만 사용")
    parser.add_argument("--no-sysfs", action="store_true", help="추가 sysfs 조회를 건너뛰고 dumpsys만 사용")
    parser.add_argument("--json", action="store_true", help="사람용 요약 대신 JSON 출력")
    parser.add_argument("--include-serial", action="store_true", help="JSON에 기기 시리얼번호 포함 (기본값: 숨김)")
    parser.add_argument("--overwrite", action="store_true", help="--save 지정 파일이 이미 존재하면 덮어쓰기")
    parser.add_argument("--save", type=Path, metavar="FILE", help="결과를 JSON 파일로 저장")
    args = parser.parse_args()
    cli_language = args.language or windows_display_language()
    cli_text = CLI_TEXT[cli_language]
    if args.donate or args.blog:
        url = donation_url(args.language) if args.donate else BLOG_URL
        print(cli_text["browser_open"].format(url=url))
        if not webbrowser.open_new_tab(url):
            print(cli_text["browser_failed"].format(url=url), file=sys.stderr)
            return 1
        return 0
    if args.rated_mah is not None and (not math.isfinite(args.rated_mah) or not 100 <= args.rated_mah <= 30000):
        parser.error(cli_text["rated_error"])

    if not args.json:
        print(f"{APP_NAME} (Unofficial) v{APP_VERSION}")
        print(AUTHOR_NOTICE)
        print()

    try:
        serial = select_device(args.adb, args.serial)
        report = collect(args.adb, serial, args.rated_mah, args.no_sysfs)
        encoded = json.dumps(report_for_export(report, args.include_serial), ensure_ascii=False, indent=2)
        if args.json:
            print(encoded)
        else:
            display(report, cli_language)
        if args.save:
            with args.save.open("w" if args.overwrite else "x", encoding="utf-8") as handle:
                handle.write(encoded + "\n")
            print(cli_text["saved"].format(path=args.save), file=sys.stderr)
        return 0
    except (AdbError, OSError) as exc:
        locale = cli_language
        if isinstance(exc, AdbError):
            detail = localized_adb_error(exc, locale)
        elif locale == "ja":
            detail = "ファイルにアクセスできないか、ADBを実行できません。アクセス権を確認してください。"
        elif locale == "en":
            detail = "Unable to access a file or run ADB. Check permissions."
        else:
            detail = "파일에 접근하거나 ADB를 실행하지 못했습니다. 권한을 확인하세요."
        prefix = cli_text["error_prefix"]
        print(f"{prefix}: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
