import datetime
import re
import pandas as pd
import pytz
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# ตั้งค่า URL ต่างๆ
# ---------------------------------------------------------
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1557319102630989855/E1NtZ-brNI-rVb4I7eSdChe072I62UyuOkxyv4aW8wIyd0GNwgday8qWlrXYNAWt9yX1"

# 🔴 [สำคัญ] นำ URL ของ Google Apps Script Web App ที่ได้จากการ Deploy มาใส่ที่นี่
GOOGLE_WEB_APP_URL = "https://script.google.com/macros/s/AKfycby8br03zjMvjQhF0SImHqk7SXy05iHIdFz13yF1Cwd_d3fFrXl1hnv6Lw5AxSpn4cP-1g/exec"


# =========================================================
# 🛠️ ฟังก์ชันย่อย (Helper Functions)
# =========================================================

def send_discord_notify(
    record_date, shift, rank_name, position, department, phone, timestamp
):
    """ฟังก์ชันส่งข้อความแจ้งเตือนเข้า Discord พร้อมระบบแจ้งเตือนสถานะ"""
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL.strip() == "":
        st.warning("⚠️ ยังไม่ได้กำหนด Discord Webhook URL")
        return

    payload = {
        "embeds": [
            {
                "title": f"📝 บันทึกข้อมูล WFH ({record_date} - {shift})",
                "color": 3447003,  # สีน้ำเงิน
                "fields": [
                    {
                        "name": "📅 วันที่ / รอบ",
                        "value": f"{record_date} ({shift})",
                        "inline": False,
                    },
                    {
                        "name": "👤 ยศ ชื่อ - สกุล",
                        "value": rank_name,
                        "inline": True,
                    },
                    {"name": "💼 ตำแหน่ง", "value": position, "inline": True},
                    {"name": "🏢 สังกัด", "value": department, "inline": True},
                    {"name": "📞 เบอร์โทรศัพท์", "value": phone, "inline": True},
                    {
                        "name": "🕒 เวลาบันทึกในระบบ",
                        "value": timestamp,
                        "inline": False,
                    },
                ],
                "footer": {"text": "ระบบบันทึกข้อมูล รร.สธ.ทอ."},
            }
        ]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code in [200, 204]:
            st.toast("🔔 ส่งการแจ้งเตือนเข้า Discord เรียบร้อยแล้ว!", icon="💬")
        else:
            st.error(
                f"❌ ไม่สามารถส่งข้อความเข้า Discord ได้ (Status Code: {response.status_code})\nรายละเอียด: {response.text}"
            )
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ Discord: {e}")


def save_data_via_webapp(new_row_dict):
    """ส่งข้อมูลผ่าน Google Apps Script Web App (แก้ปัญหา Concurrency และ Error 429)"""
    if not GOOGLE_WEB_APP_URL or "YOUR_SCRIPT_ID_HERE" in GOOGLE_WEB_APP_URL:
        st.error("❌ ยังไม่ได้กำหนด GOOGLE_WEB_APP_URL ให้ถูกต้อง")
        return False

    try:
        response = requests.post(GOOGLE_WEB_APP_URL, json=new_row_dict, timeout=10)
        result = response.json()
        
        if result.get("status") == "success":
            return True
        else:
            st.error(f"❌ เกิดข้อผิดพลาดจาก Google Sheets: {result.get('message')}")
            return False
    except Exception as e:
        st.error(f"❌ ไม่สามารถเชื่อมต่อกับ Web App ได้: {e}")
        return False


# =========================================================
# 🚀 ตัวแอปหลัก (Main Application)
# =========================================================

# 1. ตั้งค่าหน้าตาของแอป
st.set_page_config(
    page_title="ระบบบันทึกข้อมูลบุคลากร รร.สธ.ทอ.",
    page_icon="📝",
    layout="centered",
)

# 2. ส่วนหัวเรื่อง
st.title(
    "📝 ระบบบันทึกข้อมูลผู้ที่ปฏิบัติงานที่บ้าน (Work From Home) รร.สธ.ทอ.ยศ.ทอ."
)
st.caption("เชื่อมต่อข้อมูลผ่าน Google Apps Script Web App (เวลาประเทศไทย UTC+7)")

# เชื่อมต่อกับ Google Sheets เฉพาะสำหรับการ "อ่านข้อมูล" (แสดงตาราง/รายงาน)
conn = st.connection("gsheets", type=GSheetsConnection)

# ---------------------------------------------------------
# 3. ส่วนฟอร์มกรอกข้อมูล (ใช้ st.form ควบคุมจังหวะการส่ง)
# ---------------------------------------------------------
st.subheader("1. กรอกข้อมูลส่วนตัวและเลือกรอบการปฏิบัติงาน")

with st.form("wfh_submission_form", clear_on_submit=False):
    col_date, col_shift = st.columns(2)

    with col_date:
        date_options = ["วันที่ 12 ต.ค.69", "วันที่ 14 ต.ค.69", "วันที่ 15 ต.ค.69"]
        record_date = st.selectbox(
            "📅 เลือกวันที่ปฏิบัติงานที่บ้าน", options=date_options
        )

    with col_shift:
        shift_options = ["รอบเช้า (08:00 - 08:15)", "รอบบ่าย (13:00 - 13:15)"]
        shift = st.selectbox("⏰ เลือกรอบการบันทึก", options=shift_options)

    st.write("---")
    rank_name = st.text_input("ยศ ชื่อ - สกุล", placeholder="เช่น ร.อ. สมชาย ใจดี")
    position = st.text_input(
        "ตำแหน่ง", placeholder="เช่น ผบ.กอง, รอง ผอ.กอง, อจ.กอง, หน.ผธก. เป็นต้น"
    )

    dept_options = [
        "-- กรุณาเลือกสังกัด --",
        "กกศ.รร.สธ.ทอ.ยศ.ทอ.",
        "กทสธ.รร.สธ.ทอ.ยศ.ทอ.",
        "กนท.รร.สธ.ทอ.ยศ.ทอ.",
        "ผธก.รร.สธ.ทอ.ยศ.ทอ.",
        "ผวผ.รร.สธ.ทอ.ยศ.ทอ.",
    ]

    selected_dept = st.selectbox("สังกัด", options=dept_options)
    
    phone_raw = st.text_input(
        "หมายเลขโทรศัพท์ที่ติดต่อได้", placeholder="เช่น 0812345678", max_chars=10
    )

    st.divider()
    
    # ปุ่มกด Submit ภายใน Form
    submitted = st.form_submit_button("🚀 ยืนยันส่งข้อมูล (Submit)", type="primary")

# ประมวลผลเมื่อกดปุ่ม Submit ใน Form
if submitted:
    # ทำความสะอาดและตรวจสอบเบอร์โทรศัพท์
    phone_clean = re.sub(r"\D", "", phone_raw)
    if len(phone_clean) == 10:
        phone = re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", phone_clean)
    else:
        phone = phone_clean

    department = "" if selected_dept == "-- กรุณาเลือกสังกัด --" else selected_dept

    # ตรวจสอบความถูกต้องของข้อมูล
    if not (rank_name and position and department and phone):
        st.error("⚠️ กรุณากรอกข้อมูลให้ครบทุกช่องก่อนกดปุ่มยืนยัน!")
    elif len(phone_clean) != 10:
        st.error("⚠️ กรุณากรอกหมายเลขโทรศัพท์ให้ถูกต้องครบ 10 หลัก!")
    else:
        with st.spinner("กำลังบันทึกข้อมูลลงระบบ..."):
            # กำหนด Time Zone เป็น Asia/Bangkok (UTC+7)
            tz_bangkok = pytz.timezone("Asia/Bangkok")
            current_time = datetime.datetime.now(tz_bangkok).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # รวบรวมข้อมูลเป็น Dictionary เพื่อส่งผ่าน Web App
            row_data = {
                "record_date": record_date,
                "shift": shift,
                "timestamp": current_time,
                "rank_name": rank_name,
                "position": position,
                "department": department,
                "phone": phone,
            }

            # ส่งข้อมูลผ่าน Google Apps Script Web App
            success = save_data_via_webapp(row_data)

            if success:
                st.success(f"✅ บันทึกข้อมูลเรียบร้อยแล้ว! ({record_date} - {shift})")
                st.balloons()

                # --- ส่งข้อมูลไปยัง Discord ---
                send_discord_notify(
                    record_date,
                    shift,
                    rank_name,
                    position,
                    department,
                    phone,
                    current_time,
                )

st.divider()

# ---------------------------------------------------------
# 4. ส่วนสรุปข้อมูลแบบ Real-Time (ยังคงใช้ conn.read อ่านข้อมูลมาแสดงผลได้ปกติ)
# ---------------------------------------------------------
st.subheader("📊 รายงานข้อมูลการบันทึก WFH")

try:
    df = conn.read(ttl=0)

    if not df.empty:
        st.metric(
            label="จำนวนรายการบันทึกทั้งหมด",
            value=f"{len(df)} รายการ",
        )

        df_display = df.copy()
        df_display.index = range(1, len(df_display) + 1)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

except Exception as e:
    st.warning("ไม่สามารถโหลดข้อมูล Real-time ได้ในขณะนี้")

st.divider()
