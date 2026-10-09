"""Galaxy Battery Check desktop interface."""

from __future__ import annotations

import importlib.util
import json
import queue
import shutil
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

CORE_FILE = Path(__file__).with_name("galaxy battery check.py")
SPEC = importlib.util.spec_from_file_location("galaxy_battery_core", CORE_FILE)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Core file not found: {CORE_FILE}")
CORE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CORE
SPEC.loader.exec_module(CORE)

LANGUAGES = {"auto": "auto", "ko": "한국어", "en": "English", "ja": "日本語"}
STRINGS = {
    "ko": {
        "heading": "갤럭시 배터리 체크 (비공식)", "subtitle": "ADB 연결 · 읽기 전용 배터리 진단",
        "independent": "삼성전자에서 개발하거나 공식적으로 승인·인증한 프로그램이 아닙니다.",
        "language": "표시 언어", "auto": "자동 (Windows)", "adb": "ADB 실행 파일", "browse": "찾아보기",
        "connection": "연결 설정", "device": "연결 기기", "scan": "기기 검색", "check": "배터리 조회",
        "rated": "정격 용량 (mAh, 선택)", "summary": "배터리 건강도", "bsoh": "BSOH · 우선 확인",
        "asoc": "ASOC · 참고", "details": "상세 배터리 정보", "model": "기기 모델",
        "android_version": "Android 버전", "level_pct": "현재 충전량", "temperature_c": "현재 배터리 온도",
        "max_temperature_c": "기록된 최고 온도", "first_use_date": "최초 사용 기록일",
        "cycle_count": "충전 사이클", "charge_counter_mah": "남은 전하량",
        "extrapolated_full_mah": "완충 용량 간이 추정", "extrapolated_to_rated_pct": "정격 용량 대비 간이 추정",
        "notice": "BSOH·ASOC는 기기가 보고한 값이며 정밀 실측치가 아닙니다. 지원하지 않는 항목은 확인 불가로 표시됩니다.",
        "privacy": "진단 데이터는 PC에서 처리되며, 후원 버튼은 별도 브라우저를 엽니다.",
        "support": "후원은 선택 사항입니다.", "donate": "♥ 후원하기 (투네이션)",
        "save": "JSON 저장", "include_serial": "JSON에 시리얼번호 포함", "adb_file_invalid": "공식 Platform-Tools의 adb.exe 파일을 선택하세요.", "none": "확인 불가", "idle": "USB 디버깅을 켜고 휴대전화를 연결하세요.",
        "scanning": "ADB 기기 검색 중…", "reading": "배터리 정보를 조회하는 중…",
        "found": "연결된 기기: {count}대", "no_device": "ADB로 연결된 기기가 없습니다.",
        "done": "배터리 정보 조회 완료 · 읽기 전용", "no_adb": "ADB가 없습니다. Platform-Tools를 설치하거나 ADB 경로를 선택하세요.",
        "unauthorized": "ADB 기기 사용 불가: {detail}", "error": "조회 실패: {detail}",
        "missing_device_title": "기기 선택", "missing_device": "기기 검색 후 스마트폰을 선택하세요.",
        "rated_title": "입력 오류", "rated_error": "정격 용량은 100~30000 mAh 범위로 입력하세요.",
        "browser_error_title": "브라우저 실행 실패", "browser_error": "브라우저에서 다음 주소를 열어 주세요:\n{url}",
        "save_title": "배터리 조회 결과 저장", "save_failed": "저장 실패", "saved": "결과를 저장했습니다: {filename}",
        "adb_title": "ADB 실행 파일 선택", "author": "제작자: Sakai (클릭하면 블로그 방문)", "copyright": "© 2026 꿈을꾸는 파랑새. All rights reserved.",
        "warning": "주의: 이 프로그램의 배터리 진단 결과는 참고용입니다. 정확한 배터리 상태를 확인하려면 삼성전자 서비스센터를 방문해 주세요.",
        "cycles": "회", "auto_hint": "Windows 표시 언어를 자동으로 적용합니다.",
        "error_permission": '파일 접근 권한이 없습니다. 저장 위치 또는 파일 권한을 확인하세요.',
        "error_file_system": '파일을 저장하거나 읽지 못했습니다. 폴더 및 파일 상태를 확인하세요.',
        "error_generic": '작업 중 오류가 발생했습니다. ADB 연결 상태를 확인하세요.',
        "save_permission": '선택한 위치에 저장할 권한이 없습니다. 다른 폴더를 선택하세요.',
        "save_os": '파일을 저장하지 못했습니다. 저장 위치와 디스크 상태를 확인하세요.',
        "save_invalid": '진단 데이터를 JSON으로 저장하지 못했습니다.',
        "device_unauthorized": '승인 필요',
        "device_offline": '오프라인',
        "device_other": '연결 불가'
    },
    "en": {
        "heading": "Galaxy Battery Check (Unofficial)", "subtitle": "ADB connection · Read-only battery diagnostics",
        "independent": "Independent software. Not developed, endorsed, or certified by Samsung Electronics.",
        "language": "Display language", "auto": "Automatic (Windows)", "adb": "ADB executable", "browse": "Browse",
        "connection": "Connection", "device": "Connected device", "scan": "Find devices", "check": "Check battery",
        "rated": "Rated capacity (mAh, optional)", "summary": "Battery health", "bsoh": "BSOH · Primary",
        "asoc": "ASOC · Reference", "details": "Battery details", "model": "Device model",
        "android_version": "Android version", "level_pct": "Battery level", "temperature_c": "Current temperature",
        "max_temperature_c": "Recorded max. temperature", "first_use_date": "First-use date",
        "cycle_count": "Charge cycles", "charge_counter_mah": "Remaining charge",
        "extrapolated_full_mah": "Estimated full capacity", "extrapolated_to_rated_pct": "Estimated vs. rated capacity",
        "notice": "BSOH/ASOC are device-reported, not laboratory measurements. Unsupported fields are marked as unavailable.",
        "privacy": "Diagnostics are processed locally. The donation button opens a separate browser window.",
        "support": "Donations are optional.", "donate": "♥ Support on Ko-fi",
        "save": "Save JSON", "include_serial": "Include serial in JSON", "adb_file_invalid": "Select adb.exe from official Platform-Tools.", "none": "Unavailable", "idle": "Enable USB debugging and connect your phone.",
        "scanning": "Scanning for ADB devices…", "reading": "Reading battery information…",
        "found": "Connected devices: {count}", "no_device": "No connected ADB devices found.",
        "done": "Battery information received · Read-only", "no_adb": "ADB not found. Install Platform-Tools or select the ADB executable.",
        "unauthorized": "ADB device unavailable: {detail}", "error": "Check failed: {detail}",
        "missing_device_title": "Select device", "missing_device": "Search for and select a phone first.",
        "rated_title": "Invalid input", "rated_error": "Enter a rated capacity between 100 and 30000 mAh.",
        "browser_error_title": "Unable to open browser", "browser_error": "Open this URL manually:\n{url}",
        "save_title": "Save battery report", "save_failed": "Save failed", "saved": "Report saved: {filename}",
        "adb_title": "Select ADB executable", "author": "Developer: Sakai (visit blog)", "copyright": "© 2026 꿈을꾸는 파랑새. All rights reserved.",
        "warning": "Caution: Battery diagnostic results from this program are for reference only. For an accurate assessment, please contact Samsung Support or a Samsung-authorized repair provider.",
        "cycles": "cycles", "auto_hint": "Uses the Windows display language automatically.",
        "error_permission": 'Access denied. Check the folder or file permissions.',
        "error_file_system": 'Unable to read or save a file. Check the folder and file status.',
        "error_generic": 'An unexpected error occurred. Check the ADB connection.',
        "save_permission": 'You do not have permission to save here. Choose another folder.',
        "save_os": 'Unable to save the file. Check the destination and disk status.',
        "save_invalid": 'Unable to save the diagnostic report as JSON.',
        "device_unauthorized": 'authorization required',
        "device_offline": 'offline',
        "device_other": 'not available'
    },
    "ja": {
        "heading": "Galaxy Battery Check（非公式）", "subtitle": "ADB接続 · 読み取り専用のバッテリー診断",
        "independent": "個人開発の非公式ツールです。Samsung Electronicsが開発・承認・認定したものではありません。",
        "language": "表示言語", "auto": "自動 (Windows)", "adb": "ADB実行ファイル", "browse": "参照",
        "connection": "接続設定", "device": "接続デバイス", "scan": "デバイス検索", "check": "バッテリー確認",
        "rated": "定格容量 (mAh、任意)", "summary": "バッテリー状態", "bsoh": "BSOH · 優先",
        "asoc": "ASOC · 参考", "details": "バッテリー詳細", "model": "機種",
        "android_version": "Androidバージョン", "level_pct": "バッテリー残量", "temperature_c": "現在の温度",
        "max_temperature_c": "記録された最高温度", "first_use_date": "初回使用日",
        "cycle_count": "充電サイクル", "charge_counter_mah": "残存電荷量",
        "extrapolated_full_mah": "満充電容量の簡易推定", "extrapolated_to_rated_pct": "定格容量比の簡易推定",
        "notice": "BSOH・ASOCは端末が報告する値であり、精密測定値ではありません。非対応の項目は取得不可と表示します。",
        "privacy": "診断データはPC内で処理されます。支援ボタンは外部ブラウザーを開きます。",
        "support": "支援は任意です。", "donate": "♥ Ko-fiで支援する",
        "save": "JSONを保存", "include_serial": "JSONにシリアル番号を含める", "adb_file_invalid": "公式Platform-Toolsのadb.exeを選択してください。", "none": "取得不可", "idle": "USBデバッグを有効にしてスマートフォンを接続してください。",
        "scanning": "ADBデバイスを検索中…", "reading": "バッテリー情報を取得中…",
        "found": "接続デバイス: {count}台", "no_device": "ADBで接続されたデバイスがありません。",
        "done": "バッテリー情報の取得完了 · 読み取り専用", "no_adb": "ADBが見つかりません。Platform-Toolsを導入するかADBの場所を選択してください。",
        "unauthorized": "ADBデバイスを使用できません: {detail}", "error": "取得失敗: {detail}",
        "missing_device_title": "デバイス選択", "missing_device": "デバイスを検索して選択してください。",
        "rated_title": "入力エラー", "rated_error": "定格容量は100～30000 mAhの数値を入力してください。",
        "browser_error_title": "ブラウザーを開けません", "browser_error": "次のURLを手動で開いてください:\n{url}",
        "save_title": "バッテリー診断結果を保存", "save_failed": "保存失敗", "saved": "保存しました: {filename}",
        "adb_title": "ADB実行ファイルを選択", "author": "制作者: Sakai（ブログを開く）", "copyright": "© 2026 꿈을꾸는 파랑새. All rights reserved.",
        "warning": "注意：本プログラムのバッテリー診断結果は参考情報です。正確なバッテリー状態を確認したい場合は、Samsungサポート、またはご利用の通信事業者の修理窓口にご相談ください。",
        "cycles": "回", "auto_hint": "Windowsの表示言語を自動的に適用します。",
        "error_permission": 'アクセス権がありません。フォルダーやファイルの権限を確認してください。',
        "error_file_system": 'ファイルの読み書きに失敗しました。保存先とファイルの状態を確認してください。',
        "error_generic": '予期しないエラーが発生しました。ADBの接続を確認してください。',
        "save_permission": 'この場所には保存する権限がありません。別のフォルダーを選択してください。',
        "save_os": 'ファイルを保存できません。保存先とディスクの状態を確認してください。',
        "save_invalid": '診断データをJSON形式で保存できません。',
        "device_unauthorized": '承認が必要',
        "device_offline": 'オフライン',
        "device_other": '使用不可'
    }
}


def find_adb() -> str:
    """Only auto-discover ADB on PATH; never auto-run a same-folder executable."""
    found = shutil.which("adb")
    if not found:
        return ""
    resolved = Path(found).resolve()
    app_dir = Path(__file__).resolve().parent
    if not resolved.is_file() or resolved.parent in {app_dir, app_dir / "platform-tools"}:
        return ""
    return str(resolved)


class BatteryWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.load_icon()
        self.language_mode = "auto"
        self.language = CORE.windows_display_language()
        self.data: dict[str, Any] | None = None
        self.results: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.busy = False
        self.status_key = "idle"
        self.status_args: dict[str, Any] = {}
        self.last_error: Exception | None = None
        self.denied_devices: list[tuple[str, str]] = []
        self.elements: dict[str, Any] = {}
        self.device_serials: list[str] = []
        self.row_names = ["model", "android_version", "level_pct", "temperature_c", "max_temperature_c", "first_use_date", "cycle_count", "charge_counter_mah", "extrapolated_full_mah", "extrapolated_to_rated_pct"]

        root.geometry("920x770")
        root.minsize(740, 660)
        root.configure(bg="#f4f6fa")
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#f4f6fa")
        style.configure("TLabel", background="#f4f6fa", font=("Segoe UI", 10))
        style.configure("TLabelframe", background="#f4f6fa")
        style.configure("TLabelframe.Label", background="#f4f6fa", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(9, 6))
        style.configure("TCombobox", padding=4)
        style.configure("Heading.TLabel", font=("Segoe UI", 19, "bold"), foreground="#152a44")
        style.configure("Muted.TLabel", foreground="#526176")
        style.configure("Footer.TLabel", font=("Segoe UI", 9), foreground="#526176")
        style.configure("Link.TLabel", font=("Segoe UI", 9, "underline"), foreground="#1760a5")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 7))
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        footer = ttk.Frame(root, padding=(18, 10, 18, 12))
        footer.pack(side="bottom", fill="x")
        footer_border = tk.Frame(root, bg="#d4deeb", height=1)
        footer_border.pack(side="bottom", fill="x")
        self.footer = footer

        status_line = ttk.Frame(footer)
        status_line.pack(fill="x", pady=(0, 7))
        self.status_var = tk.StringVar()
        ttk.Label(status_line, textvariable=self.status_var, style="Footer.TLabel", wraplength=590).pack(side="left", fill="x", expand=True)
        self.elements["save"] = ttk.Button(status_line, command=self.save, state="disabled")
        self.elements["save"].pack(side="right", padx=(12, 0))
        self.include_serial_var = tk.BooleanVar(value=False)
        self.elements["include_serial"] = ttk.Checkbutton(status_line, variable=self.include_serial_var)
        self.elements["include_serial"].pack(side="right", padx=(8, 0))

        action_line = ttk.Frame(footer)
        action_line.pack(fill="x")
        self.elements["support"] = ttk.Label(action_line, style="Footer.TLabel")
        self.elements["support"].pack(side="left", anchor="center")
        self.elements["donate"] = tk.Button(
            action_line, command=self.open_donation, bg="#147a52", fg="#ffffff",
            activebackground="#0d6040", activeforeground="#ffffff", relief="flat",
            borderwidth=0, padx=18, pady=9, font=("Segoe UI", 10, "bold"), cursor="hand2"
        )
        self.elements["donate"].pack(side="right", padx=(8, 0))

        legal_line = ttk.Frame(footer)
        legal_line.pack(fill="x", pady=(7, 0))
        self.elements["author"] = ttk.Label(legal_line, style="Link.TLabel", cursor="hand2")
        self.elements["author"].pack(side="left")
        self.elements["author"].bind("<Button-1>", self.open_author_blog)
        self.elements["copyright"] = ttk.Label(legal_line, style="Footer.TLabel")
        self.elements["copyright"].pack(side="right")

        warning_line = ttk.Frame(footer)
        warning_line.pack(side="bottom", fill="x", pady=(8, 0))
        # tk.Message wraps the complete disclaimer within its pixel width.
        # A ttk.Label can retain an oversized requested width and clip long
        # translations (notably English) instead of displaying the last line.
        self.elements["warning"] = tk.Message(
            warning_line, width=640, font=("Segoe UI", 9, "bold"),
            foreground="#b91c1c", background="#f4f6fa", justify="left",
            anchor="w", padx=0, pady=0, borderwidth=0, highlightthickness=0,
        )
        self.elements["warning"].pack(side="left", fill="x", expand=True)
        warning_line.bind(
            "<Configure>",
            lambda event: self.elements["warning"].configure(width=max(200, event.width - 12)),
        )

        viewport = ttk.Frame(root)
        viewport.pack(side="top", fill="both", expand=True)
        self.main_canvas = tk.Canvas(viewport, bg="#f4f6fa", highlightthickness=0, borderwidth=0)
        main_scroll = ttk.Scrollbar(viewport, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=main_scroll.set)
        main_scroll.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        main = ttk.Frame(self.main_canvas, padding=(18, 13, 18, 8))
        content_id = self.main_canvas.create_window((0, 0), window=main, anchor="nw")
        main.bind("<Configure>", lambda event: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.bind("<Configure>", lambda event: self.main_canvas.itemconfigure(content_id, width=event.width))
        header = ttk.Frame(main)
        header.pack(fill="x")
        heading = ttk.Frame(header)
        heading.pack(side="left", fill="x", expand=True)
        self.elements["heading"] = ttk.Label(heading, style="Heading.TLabel", wraplength=480)
        self.elements["heading"].pack(anchor="w")
        self.elements["subtitle"] = ttk.Label(heading, style="Muted.TLabel")
        self.elements["subtitle"].pack(anchor="w", pady=(3, 0))
        language_box = ttk.Frame(header)
        language_box.pack(side="right", anchor="ne")
        self.elements["language"] = ttk.Label(language_box)
        self.elements["language"].pack(anchor="w")
        self.lang_var = tk.StringVar()
        self.lang_combo = ttk.Combobox(language_box, textvariable=self.lang_var, width=18, state="readonly")
        self.lang_combo.pack(anchor="e", pady=(3, 0))
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        # The "Unofficial" suffix wraps at smaller window widths, rather than
        # colliding with the language selector.
        header.bind("<Configure>", lambda event: self.elements["heading"].configure(
            wraplength=max(210, event.width - 235)))

        independence_line = ttk.Frame(main)
        independence_line.pack(fill="x", pady=(5, 0))
        self.elements["independent"] = tk.Message(
            independence_line, width=500, font=("Segoe UI", 9),
            foreground="#715024", background="#f4f6fa", justify="left",
            anchor="w", padx=0, pady=0, borderwidth=0, highlightthickness=0,
        )
        self.elements["independent"].pack(side="left", fill="x", expand=True)
        independence_line.bind("<Configure>", lambda event: self.elements["independent"].configure(
            width=max(210, event.width - 12)))

        connection = ttk.LabelFrame(main, padding=11)
        connection.pack(fill="x", pady=(12, 10))
        self.elements["connection"] = connection
        connection.columnconfigure(1, weight=1)
        self.elements["adb"] = ttk.Label(connection)
        self.elements["adb"].grid(row=0, column=0, sticky="w", padx=(0, 12), pady=4)
        self.adb_var = tk.StringVar(value=find_adb())
        ttk.Entry(connection, textvariable=self.adb_var).grid(row=0, column=1, sticky="ew", pady=4)
        self.elements["browse"] = ttk.Button(connection, command=self.browse_adb)
        self.elements["browse"].grid(row=0, column=2, padx=(10, 0), pady=4)
        self.elements["device"] = ttk.Label(connection)
        self.elements["device"].grid(row=1, column=0, sticky="w", padx=(0, 12), pady=4)
        self.device_var = tk.StringVar()
        self.devices = ttk.Combobox(connection, textvariable=self.device_var, state="readonly")
        self.devices.grid(row=1, column=1, sticky="ew", pady=4)
        self.elements["scan"] = ttk.Button(connection, command=self.scan)
        self.elements["scan"].grid(row=1, column=2, padx=(10, 0), pady=4)
        self.elements["rated"] = ttk.Label(connection)
        self.elements["rated"].grid(row=2, column=0, sticky="w", padx=(0, 12), pady=4)
        self.rated_var = tk.StringVar()
        ttk.Entry(connection, textvariable=self.rated_var).grid(row=2, column=1, sticky="ew", pady=4)
        self.elements["check"] = ttk.Button(connection, command=self.check, style="Accent.TButton")
        self.elements["check"].grid(row=2, column=2, padx=(10, 0), pady=4)

        self.elements["summary"] = ttk.Label(main, font=("Segoe UI", 11, "bold"))
        self.elements["summary"].pack(anchor="w", pady=(4, 6))
        cards = ttk.Frame(main)
        cards.pack(fill="x")
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)
        self.cards = {}
        for index, key in enumerate(("bsoh", "asoc")):
            card = tk.Frame(cards, bg="#e6f0fa" if index == 0 else "#e9eef5", padx=15, pady=10)
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 8) if index == 0 else (8, 0))
            header_text = tk.Label(card, bg=card["bg"], fg="#40546b", font=("Segoe UI", 10, "bold"), anchor="w")
            header_text.pack(fill="x")
            value = tk.Label(card, text="—", bg=card["bg"], fg="#10365e", font=("Segoe UI", 24, "bold"), anchor="w")
            value.pack(fill="x", pady=(6, 0))
            self.cards[key] = (header_text, value)

        self.elements["details"] = ttk.Label(main, font=("Segoe UI", 11, "bold"))
        self.elements["details"].pack(anchor="w", pady=(13, 6))
        table_box = ttk.Frame(main)
        table_box.pack(fill="both", expand=True)
        self.table = ttk.Treeview(table_box, columns=("value",), show="tree headings", selectmode="none", height=6)
        self.table.heading("#0", text="")
        self.table.heading("value", text="")
        self.table.column("#0", width=280, stretch=True)
        self.table.column("value", width=320, stretch=True, anchor="e")
        table_scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=table_scroll.set)
        table_scroll.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        for key in self.row_names:
            self.table.insert("", "end", iid=key, text="", values=("—",))

        self.elements["notice"] = ttk.Label(main, style="Footer.TLabel", wraplength=750)
        self.elements["notice"].pack(fill="x", pady=(10, 0))
        self.elements["privacy"] = ttk.Label(main, style="Footer.TLabel", wraplength=750)
        self.elements["privacy"].pack(fill="x", pady=(1, 7))
        self.translate()
        root.after(100, self.process_results)
        if self.adb_var.get():
            root.after(350, self.scan)
        else:
            self.set_status("no_adb")

    def load_icon(self) -> None:
        icon = Path(__file__).with_name("galaxy battery check.ico")
        image = Path(__file__).with_name("galaxy battery check.png")
        if sys.platform == "win32" and icon.is_file():
            try:
                self.root.iconbitmap(default=str(icon))
            except tk.TclError:
                pass
        if image.is_file():
            try:
                self.app_icon_image = tk.PhotoImage(file=str(image))
                self.root.iconphoto(True, self.app_icon_image)
            except tk.TclError:
                pass

    def t(self, key: str, **args: Any) -> str:
        text = STRINGS[self.language][key]
        return text.format(**args) if args else text

    def set_status(self, key: str, **args: Any) -> None:
        self.status_key, self.status_args = key, args
        if key != "error":
            self.last_error = None
        self.status_var.set(self.t(key, **args))

    def error_message(self, exc: Exception) -> str:
        if isinstance(exc, CORE.AdbError):
            return CORE.localized_adb_error(exc, self.language)
        if isinstance(exc, FileNotFoundError):
            return self.t("no_adb")
        if isinstance(exc, PermissionError):
            return self.t("error_permission")
        if isinstance(exc, OSError):
            return self.t("error_file_system")
        return self.t("error_generic")

    def denied_description(self) -> str:
        names = {
            "unauthorized": self.t("device_unauthorized"),
            "offline": self.t("device_offline"),
        }
        return ", ".join(
            f"{serial} ({names.get(state, self.t('device_other'))})"
            for serial, state in self.denied_devices
        )

    def translate(self) -> None:
        self.root.title(f"{self.t('heading')} v{CORE.APP_VERSION} · {CORE.COPYRIGHT_HOLDER}")
        for key, widget in self.elements.items():
            widget.configure(text=self.t(key))
        color = "#147a52" if self.language == "ko" else "#1b5ec9"
        active_color = "#0d6040" if self.language == "ko" else "#154a9f"
        self.elements["donate"].configure(bg=color, activebackground=active_color)
        self.lang_combo["values"] = [self.t("auto"), LANGUAGES["ko"], LANGUAGES["en"], LANGUAGES["ja"]]
        self.lang_var.set(self.t("auto") if self.language_mode == "auto" else LANGUAGES[self.language_mode])
        for key, (label, _) in self.cards.items():
            label.configure(text=self.t(key))
        for key in self.row_names:
            self.table.item(key, text=self.t(key))
        if self.status_key == "error" and self.last_error is not None:
            self.set_status("error", detail=self.error_message(self.last_error))
        elif self.status_key == "unauthorized" and self.denied_devices:
            self.set_status("unauthorized", detail=self.denied_description())
        else:
            self.set_status(self.status_key, **self.status_args)
        if self.data is not None:
            self.render(self.data)

    def change_language(self, _event: Any = None) -> None:
        selected = self.lang_combo.current()
        self.language_mode = ("auto", "ko", "en", "ja")[selected] if 0 <= selected <= 3 else "auto"
        self.language = CORE.windows_display_language() if self.language_mode == "auto" else self.language_mode
        self.translate()

    def open_url(self, url: str) -> None:
        try:
            if not webbrowser.open_new_tab(url):
                messagebox.showerror(self.t("browser_error_title"), self.t("browser_error", url=url))
        except Exception:
            messagebox.showerror(self.t("browser_error_title"), self.t("browser_error", url=url))

    def open_donation(self) -> None:
        self.open_url(CORE.donation_url(self.language))

    def open_author_blog(self, _event: Any = None) -> None:
        self.open_url(CORE.BLOG_URL)

    def browse_adb(self) -> None:
        path = filedialog.askopenfilename(title=self.t("adb_title"), filetypes=[("ADB", "adb.exe"), ("All files", "*.*")])
        if path:
            if sys.platform == "win32" and Path(path).name.casefold() != "adb.exe":
                messagebox.showwarning(self.t("adb_title"), self.t("adb_file_invalid"))
                return
            self.adb_var.set(path)
            self.scan()

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        for key in ("scan", "check", "browse"):
            self.elements[key].configure(state="disabled" if busy else "normal")

    def start_job(self, action: str, fn: Any) -> None:
        if self.busy:
            return
        self.set_busy(True)
        def worker() -> None:
            try:
                self.results.put((action, fn()))
            except Exception as exc:
                self.results.put(("error", exc))
        threading.Thread(target=worker, daemon=True).start()

    def scan(self) -> None:
        self.set_status("scanning")
        adb = self.adb_var.get().strip()
        if not adb:
            self.set_status("no_adb")
            return
        def work() -> tuple[list[str], list[tuple[str, str]]]:
            output = CORE.adb_call(adb, ["devices", "-l"])
            connected, denied = [], []
            for line in (output or "").splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    if parts[1] == "device":
                        connected.append(parts[0])
                    else:
                        denied.append((parts[0], parts[1]))
            return connected, denied
        self.start_job("scan", work)

    def check(self) -> None:
        serial = self.device_var.get().strip()
        if not serial:
            messagebox.showwarning(self.t("missing_device_title"), self.t("missing_device"))
            return
        raw = self.rated_var.get().strip()
        try:
            rated = float(raw) if raw else None
            if rated is not None and not 100 <= rated <= 30000:
                raise ValueError
        except ValueError:
            messagebox.showwarning(self.t("rated_title"), self.t("rated_error"))
            return
        self.set_status("reading")
        adb = self.adb_var.get().strip()
        if not adb:
            self.set_status("no_adb")
            return
        self.start_job("check", lambda: CORE.collect(adb, serial, rated, skip_sysfs=False))

    def process_results(self) -> None:
        try:
            while True:
                action, value = self.results.get_nowait()
                self.set_busy(False)
                if action == "error":
                    self.last_error = value
                    self.set_status("error", detail=self.error_message(value))
                elif action == "scan":
                    connected, denied = value
                    self.denied_devices = denied
                    current = self.device_var.get()
                    self.devices["values"] = connected
                    self.device_var.set(current if current in connected else (connected[0] if connected else ""))
                    if connected:
                        self.set_status("found", count=len(connected))
                    elif denied:
                        self.set_status("unauthorized", detail=self.denied_description())
                    else:
                        self.set_status("no_device")
                elif action == "check":
                    self.data = value
                    self.render(value)
                    self.elements["save"].configure(state="normal")
                    self.set_status("done")
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self.process_results)

    def fmt(self, value: Any, unit: str = "", digits: int = 1) -> str:
        if value is None or value == "":
            return self.t("none")
        if isinstance(value, float):
            return f"{value:.{digits}f}{unit}"
        return f"{value}{unit}"

    def render(self, report: dict[str, Any]) -> None:
        battery = report["battery"]
        device = report["device"]
        self.cards["bsoh"][1].configure(text=self.fmt(battery.get("bsoh_pct"), "%", 2))
        self.cards["asoc"][1].configure(text=self.fmt(battery.get("asoc_pct"), "%", 2))
        values = {
            "model": self.fmt(device.get("model")),
            "android_version": self.fmt(device.get("android_version")),
            "level_pct": self.fmt(battery.get("level_pct"), "%"),
            "temperature_c": self.fmt(battery.get("temperature_c"), " °C"),
            "max_temperature_c": self.fmt(battery.get("max_temperature_c"), " °C"),
            "first_use_date": self.fmt(battery.get("first_use_date")),
            "cycle_count": self.fmt(battery.get("cycle_count"), " " + self.t("cycles"), 2),
            "charge_counter_mah": self.fmt(battery.get("charge_counter_mah"), " mAh", 2),
            "extrapolated_full_mah": self.fmt(battery.get("extrapolated_full_mah"), " mAh"),
            "extrapolated_to_rated_pct": self.fmt(battery.get("extrapolated_to_rated_pct"), "%"),
        }
        for key in self.row_names:
            self.table.item(key, values=(values[key],))

    def save(self) -> None:
        if self.data is None:
            return
        dest = filedialog.asksaveasfilename(title=self.t("save_title"), defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="galaxy battery report.json")
        if not dest:
            return
        try:
            report = json.loads(json.dumps(CORE.report_for_export(self.data, self.include_serial_var.get()), ensure_ascii=False))
            report["application"]["donation_url"] = CORE.donation_url(self.language)
            Path(dest).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except PermissionError:
            messagebox.showerror(self.t("save_failed"), self.t("save_permission"))
            return
        except OSError:
            messagebox.showerror(self.t("save_failed"), self.t("save_os"))
            return
        except (ValueError, TypeError):
            messagebox.showerror(self.t("save_failed"), self.t("save_invalid"))
            return
        self.set_status("saved", filename=Path(dest).name)


def main() -> None:
    root = tk.Tk()
    # Prevent a partially constructed Tk window from flashing at startup.
    root.withdraw()
    BatteryWindow(root)
    root.update_idletasks()
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
