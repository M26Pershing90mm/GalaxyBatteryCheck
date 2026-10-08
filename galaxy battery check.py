"""Samsung Galaxy battery diagnostics over ADB (read-only, no root required).

Requires Android SDK Platform-Tools (adb) and USB debugging authorization.
Only reports values actually exposed by the connected device.
"""

from __future__ import annotations

import argparse
import ctypes
import runpy
import json
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any


APP_NAME = "Galaxy Battery Check"
APP_VERSION = "1.4.3"
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
    """ADB is missing, disconnected, or returned an error."""


def adb_call(adb: str, args: list[str], timeout: int = 12, optional: bool = False) -> str | None:
    try:
        result = subprocess.run(
            [adb, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AdbError("adb 실행 파일을 찾지 못했습니다. Android SDK Platform-Tools를 설치하거나 --adb 경로를 지정하세요.") from exc
    except subprocess.TimeoutExpired as exc:
        if optional:
            return None
        raise AdbError(f"ADB 응답 시간 초과: {' '.join(args)}") from exc

    if result.returncode != 0:
        if optional:
            return None
        message = (result.stderr or result.stdout).strip() or "원인 불명 오류"
        raise AdbError(f"ADB 오류: {message}")
    return result.stdout.strip()


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
            raise AdbError(f"지정한 기기({serial})가 ADB 목록에 없습니다. adb devices -l 명령으로 확인하세요.")
        if devices[serial] != "device":
            raise AdbError(f"기기 {serial} 상태가 '{devices[serial]}'입니다. 스마트폰에서 USB 디버깅을 허용하세요.")
        return serial

    connected = [key for key, state in devices.items() if state == "device"]
    if len(connected) == 1:
        return connected[0]
    if len(connected) > 1:
        raise AdbError("기기가 여러 대 연결되어 있습니다. --serial SERIAL 옵션으로 하나를 선택하세요.")
    if devices:
        states = ", ".join(f"{key}={state}" for key, state in devices.items())
        raise AdbError(f"사용 가능한 기기가 없습니다({states}). USB 디버깅 승인 여부를 확인하세요.")
    raise AdbError("연결된 Android 기기가 없습니다. USB 케이블과 디버깅 설정을 확인하세요.")


def number_from_field(text: str, field: str) -> float | None:
    """Read a whole-line `field: 98.710` or `field: [99]` value."""
    pattern = rf"(?mi)^\s*{re.escape(field)}\s*:\s*\[?\s*(-?\d+(?:\.\d+)?)"
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None


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
    return float(match.group(1)) if match else None


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
        raise AdbError("배터리 데이터가 정상적으로 반환되지 않았습니다.")

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


def display(report: dict[str, Any]) -> None:
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
    print("※ 비공식 독립 개발 도구이며 삼성전자에서 승인·인증한 프로그램이 아닙니다.")
    print("※ BSOH/ASOC는 기기 보고값이며 정밀 실측치가 아닙니다.")
    print("※ 충전량 역산은 참고용으로, BSOH/ASOC 대체값이 아닙니다.")
    print("※ 최고 온도와 최초 사용일의 기록 범위는 보장되지 않습니다.")
    print("※ 표시되지 않는 필드는 지원하지 않거나 읽기 권한이 없을 수 있습니다.")
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
    parser.add_argument("--save", type=Path, metavar="FILE", help="결과를 JSON 파일로 저장")
    args = parser.parse_args()
    if args.donate or args.blog:
        url = donation_url(args.language) if args.donate else BLOG_URL
        print(f"브라우저로 열기: {url}")
        if not webbrowser.open_new_tab(url):
            print(f"브라우저를 자동으로 열지 못했습니다. 주소를 직접 열어주세요: {url}", file=sys.stderr)
            return 1
        return 0
    if args.rated_mah is not None and not 100 <= args.rated_mah <= 30000:
        parser.error("--rated-mah는 100~30000 범위의 mAh 값이어야 합니다.")

    if not args.json:
        print(f"{APP_NAME} (Unofficial) v{APP_VERSION}")
        print(AUTHOR_NOTICE)
        print()

    try:
        serial = select_device(args.adb, args.serial)
        report = collect(args.adb, serial, args.rated_mah, args.no_sysfs)
        encoded = json.dumps(report, ensure_ascii=False, indent=2)
        if args.json:
            print(encoded)
        else:
            display(report)
        if args.save:
            args.save.write_text(encoded + "\n", encoding="utf-8")
            print(f"JSON 파일 저장: {args.save}", file=sys.stderr)
        return 0
    except (AdbError, OSError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
