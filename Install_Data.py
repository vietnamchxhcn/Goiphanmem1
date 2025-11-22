#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ==================== CAU HINH ====================
SYMBOLS = ["HNX-INDEX"]
API_ENDPOINT = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

OUTPUT_FOLDER = Path("data_HNXINDEX")
OUTPUT_FILE = OUTPUT_FOLDER / "HNXINDEX_Lichsu.xlsx"
OUTPUT_FOLDER.mkdir(exist_ok=True)

THREAD_COUNT = 8
REQUEST_TIMEOUT = 15
RETRY_COUNT = 3
PAGE_SIZE = 10000

HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://cafef.vn/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}
# ================================================


class CafefDataFetcher:
    @staticmethod
    def fetch_symbol_data(symbol: str) -> Optional[pd.DataFrame]:
        params = {
            "Symbol": symbol,
            "StartDate": "01/01/2020",
            "EndDate": "today",
            "PageIndex": 1,
            "PageSize": PAGE_SIZE
        }

        for attempt in range(1, RETRY_COUNT + 1):
            try:
                with requests.get(
                    API_ENDPOINT,
                    params=params,
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT
                ) as resp:
                    if resp.status_code != 200:
                        print(f"  [{symbol}] HTTP {resp.status_code} (lan {attempt})")
                        if attempt < RETRY_COUNT:
                            time.sleep(2)
                        continue

                    data = resp.json()
                    records = data.get("Data", [])

                    if not records:
                        print(f"  [{symbol}] Khong co du lieu tra ve")
                        return None

                    df = pd.DataFrame(records)
                    if df.empty:
                        return None

                    df = CafefDataFetcher._clean_and_transform(df, symbol)
                    print(f"  [{symbol}] Lay thanh cong: {len(df)} dong")
                    return df

            except requests.RequestException as e:
                print(f"  [{symbol}] Loi mang (lan {attempt}): {e}")
                if attempt < RETRY_COUNT:
                    time.sleep(2)
            except json.JSONDecodeError:
                print(f"  [{symbol}] JSON loi dinh dang (lan {attempt})")
                if attempt < RETRY_COUNT:
                    time.sleep(2)

        print(f"  [{symbol}] That bai sau {RETRY_COUNT} lan thu")
        return None

    @staticmethod
    def _clean_and_transform(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        df["Symbol"] = symbol

        column_mapping = {
            "Ngay": "Date",
            "GiaDieuChinh": "Close_Adj",
            "GiaDongCua": "Close",
            "ThayDoi": "Change",
            "PhanTramThayDoi": "Change_Pct",
            "KLGD": "Volume",
            "GiaMoCua": "Open",
            "GiaCaoNhat": "High",
            "GiaThapNhat": "Low"
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

        if "Date" in df.columns and not df["Date"].isna().all():
            df = df.sort_values("Date").reset_index(drop=True)

        return df


class ExcelExporter:
    @staticmethod
    def export(data_dict: Dict[str, pd.DataFrame]) -> None:
        if not data_dict:
            print("Khong co du lieu de xuat. Tao file thong bao...")
            empty_df = pd.DataFrame({"Thong bao": ["Khong lay duoc du lieu tu API"]})
            with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
                empty_df.to_excel(writer, sheet_name="Thong_bao", index=False)
            print(f"File mau da tao: {OUTPUT_FILE}")
            return

        print(f"Dang ghi {len(data_dict)} sheet vao Excel...")
        with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
            for symbol, df in data_dict.items():
                if df is None or df.empty:
                    continue
                sheet_name = str(symbol)[:31].replace("/", "_").replace("\\", "_")
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"Da luu file: {OUTPUT_FILE.resolve()}")


def print_banner():
    print("=" * 70)
    print(" " * 15 + "LAY DU LIEU LICH SU HNX-INDEX -> EXCEL")
    print("=" * 70)


def main():
    print_banner()
    start_time = time.time()

    results: Dict[str, pd.DataFrame] = {}
    failed_symbols: List[str] = []

    print(f"Bat dau lay du lieu cho {len(SYMBOLS)} ma (toi da {THREAD_COUNT} luong)...\n")

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as pool:
        future_to_symbol = {
            pool.submit(CafefDataFetcher.fetch_symbol_data, sym): sym
            for sym in SYMBOLS
        }

        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                df = future.result()
                if df is not None:
                    results[symbol] = df
                else:
                    failed_symbols.append(symbol)
            except Exception as e:
                print(f"  Loi khong mong muon voi {symbol}: {e}")
                failed_symbols.append(symbol)

    print("\n" + "=" * 70)
    print(f"HOAN TAT: {len(results)}/{len(SYMBOLS)} ma thanh cong")
    if failed_symbols:
        print(f"That bai: {', '.join(failed_symbols)}")
    print("=" * 70)

    ExcelExporter.export(results)

    elapsed = time.time() - start_time
    print(f"\nThoi gian thuc thi: {elapsed:.2f} giay")


if __name__ == "__main__":
    main()