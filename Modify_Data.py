#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import ast
import re
from pathlib import Path
import warnings
from typing import Optional, Dict, Tuple

warnings.filterwarnings("ignore")

# ==================== CAU HINH ====================
# Đảm bảo đường dẫn này đúng với máy của bạn
INPUT_PATH = Path("C:\\Users\\nguye\\OneDrive\\Documents\\python\\CK GOI1\\data_HNX30_STOCKS\\HNX30_STOCKS_Lichsu.xlsx")

# Python sẽ tự động tạo thư mục nếu đường dẫn này chưa tồn tại
OUTPUT_PATH = Path("C:\\Users\\nguye\\OneDrive\\Documents\\python\\CK GOI1\\data_HNX30_STOCKS\\HNX30_STOCKS_Lichsu_Clean.xlsx")

TARGET_SHEETS = [
    "DVM", "DP3", "CAP", "DTD", "CEO", "BVS", "DHT", "DXP", "HGM", "HUT",
    "IDC", "L18", "L14", "IDV", "LAS", "LHC", "MBS", "NTP", "PSD", "PLC",
    "PVB", "PVI", "PVC", "PVS", "SHS", "SLS", "TMB", "TNG", "VC3", "VCS"
]

REQUIRED_COLUMNS = [
    "Ngay", "GiaMoCua", "GiaCaoNhat", "GiaThapNhat", "GiaDongCua",
    "GiaDieuChinh", "ThayDoi", "PhanTramThayDoi", "KhoiLuongKhopLenh",
    "GiaTriKhopLenh", "KLThoaThuan", "GtThoaThuan"
]

RENAME_MAP = {
    "Ngay": "Date",
    "GiaMoCua": "Open",
    "GiaCaoNhat": "High",
    "GiaThapNhat": "Low",
    "GiaDongCua": "Close",
    "GiaDieuChinh": "Close_Adj",
    "ThayDoi": "Change",
    "PhanTramThayDoi": "Change_Pct",
    "KhoiLuongKhopLenh": "Volume",
    "GiaTriKhopLenh": "Value",
    "KLThoaThuan": "Vol_Agree",
    "GtThoaThuan": "Val_Agree",
}
# ================================================


class DataCleaner:
    @staticmethod
    def extract_change_info(text: str) -> Tuple[Optional[float], Optional[float]]:
        if not isinstance(text, str):
            return None, None
        change_match = re.search(r"([-+]?\d*\.?\d+)", text)
        pct_match = re.search(r"\(([-+]?\d*\.?\d+)", text)
        change = float(change_match.group(0)) if change_match else None
        pct = float(pct_match.group(1)) if pct_match else None
        return change, pct

    @staticmethod
    def safe_parse_dict(cell: any) -> Optional[Dict]:
        if not isinstance(cell, str) or "{" not in cell:
            return None
        start_idx = cell.find("{")
        dict_str = cell[start_idx:]
        try:
            return ast.literal_eval(dict_str)
        except (ValueError, SyntaxError):
            return None

    @staticmethod
    def find_dict_column(df: pd.DataFrame) -> Optional[str]:
        for col in df.columns:
            sample = df[col].dropna().astype(str)
            if sample.empty:
                continue
            first_val = sample.iloc[0]
            if first_val.count("{") >= 1 and first_val.count("}") >= 1:
                return col
        return None
    
    @staticmethod
    def fix_last_day_zero_close(df: pd.DataFrame) -> pd.DataFrame:
        """
        Kiem tra dong du lieu cuoi cung (ngay moi nhat).
        Neu Close == 0 thi gan Close = Open.
        """
        if df.empty:
            return df
        
        if "Close" not in df.columns or "Open" not in df.columns:
            return df

        last_idx = df.index[-1]
        
        try:
            close_val = float(df.at[last_idx, "Close"])
            open_val = df.at[last_idx, "Open"]
            
            if close_val == 0:
                # print(f"  [FIX] Phat hien Close=0 tai ngay {df.at[last_idx, 'Date']}. Cap nhat Close = {open_val}")
                df.at[last_idx, "Close"] = open_val
        except Exception as e:
            print(f"  [FIX ERROR] Khong the xu ly gia 0: {e}")
            
        return df

    @staticmethod
    def process_dataframe(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        print(f"  Xu ly sheet: {sheet_name} ({len(df)} dong)")

        dict_column = DataCleaner.find_dict_column(df)
        if not dict_column:
            print("  Khong tim thay cot chua dict.")
            return pd.DataFrame()

        df["parsed_dict"] = df[dict_column].apply(DataCleaner.safe_parse_dict)
        valid_rows = df[df["parsed_dict"].notna()].copy()

        if valid_rows.empty:
            print("  Khong co dict hop le.")
            return pd.DataFrame()

        expanded = pd.json_normalize(valid_rows["parsed_dict"])
        base_df = valid_rows.drop(columns=[dict_column, "parsed_dict"], errors="ignore")
        combined = pd.concat([base_df.reset_index(drop=True), expanded.reset_index(drop=True)], axis=1)

        available_cols = [c for c in REQUIRED_COLUMNS if c in combined.columns]
        result = combined[available_cols].copy()

        if "ThayDoi" in result.columns:
            changes = result["ThayDoi"].apply(DataCleaner.extract_change_info)
            result["Change"] = changes.apply(lambda x: x[0])
            result["Change_Pct"] = changes.apply(lambda x: x[1])
            result = result.drop(columns=["ThayDoi"], errors="ignore")

        result = result.rename(columns=RENAME_MAP)

        if "Date" in result.columns:
            result["Date"] = pd.to_datetime(result["Date"], format="%d/%m/%Y", errors="coerce")
            result = result.sort_values("Date").reset_index(drop=True)

        result = DataCleaner.fix_last_day_zero_close(result)

        print(f"  Hoan tat: {len(result)} dong")
        return result


def export_to_excel(processed_data: Dict[str, pd.DataFrame]):
    if not processed_data:
        print("Khong co du lieu de xuat.")
        return

    # --- KHU VỰC SỬA LỖI ---
    # Tao thu muc cha cua file output neu no chua ton tai
    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Loi tao thu muc {OUTPUT_PATH.parent}: {e}")
        return
    # -----------------------

    print(f"Dang ghi {len(processed_data)} sheet vao file Excel...")
    print(f"Duong dan: {OUTPUT_PATH}")

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        for sheet_name, df in processed_data.items():
            if df.empty:
                pass 
            else:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Da luu file thanh cong!")


def print_header():
    print("=" * 70)
    print("TACH & CLEAN DATA - HNX30 STOCKS")
    print("=" * 70)


def main():
    if not INPUT_PATH.exists():
        print(f"Khong tim thay file dau vao: {INPUT_PATH}")
        print("Vui long kiem tra lai duong dan hoac ten file.")
        return

    print_header()

    try:
        print(f"Dang doc file: {INPUT_PATH.name} ...")
        excel_file = pd.ExcelFile(INPUT_PATH, engine="openpyxl")
    except Exception as e:
        print(f"Loi doc file Excel: {e}")
        return

    available_sheets = [s for s in excel_file.sheet_names if s in TARGET_SHEETS]
    
    if not available_sheets:
        print(f"Khong tim thay sheet nao khop voi danh sach TARGET_SHEETS.")
        return
        
    print(f"Tim thay {len(available_sheets)}/{len(TARGET_SHEETS)} sheet hop le.\n")

    cleaned_results: Dict[str, pd.DataFrame] = {}

    for sheet in available_sheets:
        try:
            raw_df = pd.read_excel(excel_file, sheet_name=sheet)
            cleaned_df = DataCleaner.process_dataframe(raw_df, sheet)
            if not cleaned_df.empty:
                cleaned_results[sheet] = cleaned_df
        except Exception as e:
            print(f"  Loi xu ly sheet {sheet}: {e}")

    export_to_excel(cleaned_results)

    print(f"\nHOAN TAT! Xu ly thanh cong {len(cleaned_results)} sheet.")


if __name__ == "__main__":
    main()