import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from plot import plot_payment_status_pie_chart



# ---------- Paths ----------
DATA_FOLDER = "data"
JSON_FOLDER = "json"
INPUT_FILE = os.path.join(JSON_FOLDER, "saved_inputs.json")
# EDITED_FILE = os.path.join(DATA_FOLDER, "edited_schedule.csv")
TRANSLATION_FILE = os.path.join(JSON_FOLDER, "translation.json")

# ---------- Default Access Key ----------
ACCESS_KEY = os.getenv('ACCESS_KEY')

# ---------- Helper Functions ----------
def load_saved_inputs():
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r") as f:
            return json.load(f)
    return {
        "loan_amount": 100000000,
        "interest_rate": 3000000,
        "duration_months": 12,
        "start_date": str(datetime.today().date()),
        "language": "en"
    }

def load_access_key():
    if os.path.exists(ACCESS_KEY_FILE):
        with open(ACCESS_KEY_FILE, "r") as f:
            return json.load(f).get("access_key")
    return None

def save_access_key(key):
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(ACCESS_KEY_FILE, "w") as f:
        json.dump({"access_key": key}, f)

def save_inputs(inputs):
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(INPUT_FILE, "w") as f:
        json.dump(inputs, f)

def end_of_month(date):
    next_month = date + relativedelta(months=1)
    return (next_month.replace(day=1) - relativedelta(days=1)).date()

def generate_schedule(principal, interest_amount, months, start_date):
    schedule = []
    start_date = pd.to_datetime(start_date)

    for i in range(months):
        payment_date = end_of_month(start_date + relativedelta(months=i))
        schedule.append({
            "Month": i + 1,
            "Date": payment_date,
            "Amount": f"{round(interest_amount, 2):,}",
            "Description": "Monthly Payment",
            "Status": "Unpaid"
        })
        # Add yearly payment at the end of every 12th month
        if (i + 1) % 12 == 0:
            yearly_payment = principal / (months / 12)
            schedule.append({
                "Month": i + 1,
                "Date": payment_date,
                "Amount": f"{round(yearly_payment, 2):,}",
                "Description": "Yearly Payment",
                "Status": "Unpaid"
            })

    return pd.DataFrame(schedule)


def load_translations():
    if os.path.exists(TRANSLATION_FILE):
        with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def translate_dataframe(df, translations):
    df.columns = [translations.get(col, col) for col in df.columns]
    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = df[column].apply(lambda x: translations.get(str(x), x))
    return df

# ---------- Streamlit App ----------
def main():
    st.title("📊 Loan Simulation Tracker")

    saved_access_key = load_access_key()
    access_key = st.text_input("Enter access key to unlock editing:", type="password", value=saved_access_key if saved_access_key else "")

    if st.button("🔒Save passwords"):
        save_access_key(access_key)
        st.success("Access key saved successfully!")

    saved_inputs = load_saved_inputs()
    translations_all = load_translations()
    key_lst = list(translations_all.keys())

    with st.sidebar:
        st.header("Loan Settings (Restricted Editing)")

        loan_amount = st.number_input("Loan Amount", min_value=0.0, value=float(saved_inputs["loan_amount"]))
        interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=float(saved_inputs["interest_rate"]))
        duration_months = st.number_input("Duration (Months)", min_value=1, value=int(saved_inputs["duration_months"]))
        start_date = st.date_input("Start Date", value=datetime.fromisoformat(saved_inputs["start_date"]).date())
        language = st.selectbox("Choose Language", key_lst, index=key_lst.index(saved_inputs.get("language", "en")))

        if access_key == ACCESS_KEY and st.button("Save Settings"):
            inputs = {
                "loan_amount": loan_amount,
                "interest_rate": interest_rate,
                "duration_months": duration_months,
                "start_date": str(start_date),
                "language": language
            }
            save_inputs(inputs)
            st.success("Settings saved successfully!")
        elif access_key == ACCESS_KEY:
            st.warning("Click 'Save Settings' to save your inputs.")


    EDITED_FILE = os.path.join(DATA_FOLDER, f"edited_schedule_{duration_months}m_{language}.csv")
    if os.path.exists(EDITED_FILE):
        schedule_df = pd.read_csv(EDITED_FILE)
        st.info(f"Loaded saved schedule: {EDITED_FILE}")
    else:
        schedule_df = generate_schedule(loan_amount, interest_rate, duration_months, start_date)
        st.warning("No saved schedule found for this duration and language. Generated a new one.")

    if language == "en":
        translations = {}
        translated_df = schedule_df.copy()
    else:
        translations = translations_all.get(language, translations_all.get("en", {}))
        translated_df = translate_dataframe(schedule_df.copy(), translations)

    # Translate header/subheader content
    schedule_label = translations.get("Loan Payment Schedule", "Loan Payment Schedule")
    year_label = translations.get("Year", "Year")
    years_label = translations.get("Years", "Years")
    year_text = year_label if duration_months == 12 else years_label

    st.subheader(f"📅 {schedule_label} for {duration_months // 12} {year_text}")

    # Translate "Status", "Paid", "Unpaid" for the column editor
    column_header_translation = translations.get("Status", "Status")
    status_translations = [
        translations.get("Paid", "Paid"),
        translations.get("Unpaid", "Unpaid")
    ]

    if access_key == ACCESS_KEY:
        edited_df = st.data_editor(
            translated_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                column_header_translation: st.column_config.SelectboxColumn(
                    column_header_translation,
                    options=status_translations,
                    required=True
                )
            }
        )

        if st.button("💾 Save Edited Table"):
            # Save current edited table
            edited_df.to_csv(EDITED_FILE, index=False)
            st.success(f"Edited schedule saved to '{EDITED_FILE}'!")

            if language == "en":
                # Also save other translated versions
                for lang_code, lang_translations in translations_all.items():
                    if lang_code == "en":
                        continue
                    translated_version = translate_dataframe(edited_df.copy(), lang_translations)
                    translated_file_path = os.path.join(DATA_FOLDER, f"edited_schedule_{lang_code}.csv")
                    translated_version.to_csv(translated_file_path, index=False)
                    st.success(f"Translated version saved: {translated_file_path}")

            else:
                # Try to reverse-translate Vietnamese back to English
                translations_vi = translations_all.get(language, {})
                reverse_translations = {v: k for k, v in translations_vi.items()}

                def reverse_translate_df(df, reverse_map):
                    df_copy = df.copy()
                    # Translate columns
                    df_copy.columns = [reverse_map.get(col, col) for col in df_copy.columns]
                    # Translate cell values
                    for column in df_copy.columns:
                        if df_copy[column].dtype == 'object':
                            df_copy[column] = df_copy[column].apply(lambda x: reverse_map.get(str(x), x))
                    return df_copy

                english_df = reverse_translate_df(edited_df, reverse_translations)
                english_path = os.path.join(DATA_FOLDER, "edited_schedule_en.csv")
                english_df.to_csv(english_path, index=False)
                st.success("Reverse-translated English schedule saved!")



    else:
        st.write(translated_df)

    st.download_button("📥 Download CSV", translated_df.to_csv(index=False), file_name="loan_schedule.csv")
    plot_payment_status_pie_chart(translated_df, language, translations_all)
        # Delete all .csv files in the data folder
    if access_key == ACCESS_KEY and st.button("🗑️ Delete All CSVs in Data Folder"):
        deleted_files = []
        for filename in os.listdir(DATA_FOLDER):
            if filename.endswith(".csv"):
                file_path = os.path.join(DATA_FOLDER, filename)
                os.remove(file_path)
                deleted_files.append(filename)
        if deleted_files:
            st.success(f"Deleted the following files:\n{', '.join(deleted_files)}")
        else:
            st.info("No CSV files found to delete.")


            
if __name__ == "__main__":
    main()
