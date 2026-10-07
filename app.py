import datetime
import re
import pandas as pd
import pytz
import requests  # ใช้สำหรับส่ง HTTP Request ไปยัง Discord
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# ตั้งค่า Discord Webhook URL
# ---------------------------------------------------------
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1557208748081283132/dwrf0Ah8EkESLkrDtZWnR7dZ6Geg0aAuj_S_72u-DmRJ9f0YVEmox-_3M-jjktSqSKSp"


def send_discord_notify(rank_name, position, department, phone, timestamp):
    """ฟังก์ชันส่งข้อความแจ้งเตือนเข้า Discord"""
    if (
        not DISCORD_WEBHOOK_URL
        or "YOUR_WEBHOOK_URL_HERE" in DISCORD_WEBHOOK_URL
    ):
        return  # ข้ามการส่งถ้ายังไม่ได้ตั้งค่า URL

    # จัดรูปแบบข้อความที่จะส่งไปยัง Discord
    payload = {
        "embeds": [
            {
                "title": "📝 มีผู้บันทึกข้อมูล Work From Home ใหม่!",
                "color": 3447003,  # สีน้ำเงิน (Decimal Color Code)
                "fields": [
                    {
                        "name": "👤 ยศ ชื่อ - สกุล",
                        "value": rank_name,
                        "inline": True,
                    },
                    {"name": "💼 ตำแหน่ง", "value": position, "inline": True},
                    {"name": "🏢 สังกัด", "value": department, "inline": True},
                    {"name": "📞 เบอร์โทรศัพท์", "value": phone, "inline": True},
                    {
                        "name": "🕒 เวลาบันทึก",
                        "value": timestamp,
                        "inline": False,
                    },
                ],
                "footer": {"text": "ระบบบันทึกข้อมูล รร.สธ.ทอ."},
            }
        ]
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการส่ง Discord Notification: {e}")

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าตาของแอป
# ---------------------------------------------------------
st.set_page_config(
    page_title="ระบบบันทึกข้อมูลบุคลากร รร.สธ.ทอ.",
    page_icon="📝",
    layout="centered"
)

# ---------------------------------------------------------
# 2. ส่วนหัวเรื่อง
# ---------------------------------------------------------
st.title("📝 ระบบบันทึกข้อมูลผู้ที่ปฏิบัติงานที่บ้าน (Work From Home) รร.สธ.ทอ.ยศ.ทอ.")
st.caption("เชื่อมต่อข้อมูลตรงกับ Google Sheets (เวลาประเทศไทย UTC+7)")

# เชื่อมต่อกับ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# ---------------------------------------------------------
# 3. ส่วนที่ 1: ฟอร์มกรอกข้อมูล
# ---------------------------------------------------------
st.subheader("1. กรอกข้อมูลส่วนตัว")

rank_name = st.text_input(
    "ยศ ชื่อ - สกุล", placeholder="เช่น ร.อ. สมชาย ใจดี"
)
position = st.text_input(
    "ตำแหน่ง", placeholder="เช่น ผบ.กอง, รอง ผอ.กอง, อจ.กอง, หน.ผธก. เป็นต้น"
)

# --- ส่วนสังกัด: เปลี่ยนเป็น st.selectbox ---
dept_options = [
    "-- กรุณาเลือกสังกัด --",
    "กกศ.รร.สธ.ทอ.ยศ.ทอ.",
    "กทสธ.รร.สธ.ทอ.ยศ.ทอ.",
    "กนท.รร.สธ.ทอ.ยศ.ทอ.",
    "ผธก.รร.สธ.ทอ.ยศ.ทอ.",
    "ผวผ.รร.สธ.ทอ.ยศ.ทอ."
     # สามารถเพิ่ม/ลบ ตัวเลือกสังกัดตามต้องการได้ที่นี่
]

selected_dept = st.selectbox("สังกัด", options=dept_options)
# หากยังไม่เลือก ให้ถือว่าค่าสังกัดเป็นค่าว่าง
department = "" if selected_dept == "-- กรุณาเลือกสังกัด --" else selected_dept

# รับค่าเบอร์โทรศัพท์ (จำกัดไม่เกิน 10 ตัวอักษร)
phone_raw = st.text_input(
    "หมายเลขโทรศัพท์ที่ติดต่อได้", placeholder="เช่น 0812345678", max_chars=10
)

# ลบตัวอักษรที่ไม่ใช่ตัวเลขออก
phone_clean = re.sub(r"\D", "", phone_raw)

# จัดฟอร์แมตเบอร์โทรศัพท์เมื่อพิมพ์ครบ 10 หลัก (0XX-XXX-XXXX)
if len(phone_clean) == 10:
    phone = re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", phone_clean)
    st.caption(f"📱 เบอร์โทรศัพท์ที่บันทึก: **{phone}**")
else:
    phone = phone_clean  # กรณีพิมพ์ยังไม่ครบ 10 หลัก ให้เก็บค่าเดิมไว้ก่อน
    if phone_clean:
        st.caption("⚠️ กรุณากรอกตัวเลขให้ครบ 10 หลัก")

st.divider()

# ---------------------------------------------------------
# 4. ส่วนที่ 2: ตรวจสอบข้อมูลก่อนส่ง & ปุ่มบันทึก
# ---------------------------------------------------------
st.subheader("2. ตรวจสอบข้อมูลก่อนยืนยัน")

if rank_name or position or department or phone:
    st.info(
        f"""
    * **ยศ ชื่อ - สกุล:** {rank_name if rank_name else '-'}
    * **ตำแหน่ง:** {position if position else '-'}
    * **สังกัด:** {department if department else '-'}
    * **เบอร์โทรศัพท์:** {phone if phone else '-'}
    """
    )
else:
    st.write("กรุณากรอกข้อมูลและตรวจสอบความถูกต้องก่อนกดยืนยัน")

# ปุ่มกด Submit ยืนยันบันทึกข้อมูล
if st.button("🚀 ยืนยันส่งข้อมูล (Submit)", type="primary"):
    if not (rank_name and position and department and phone):
        st.error("⚠️ กรุณากรอกข้อมูลให้ครบทุกช่องก่อนกดยืนยัน!")
    elif len(phone_clean) != 10:
        st.error("⚠️ กรุณากรอกหมายเลขโทรศัพท์ให้ถูกต้องครบ 10 หลัก!")
    else:
        try:
            # ดึงข้อมูลเดิมจาก Google Sheets
            existing_data = conn.read(ttl=0)

            # กำหนด Time Zone เป็น Asia/Bangkok (UTC+7)
            tz_bangkok = pytz.timezone("Asia/Bangkok")
            current_time = datetime.datetime.now(tz_bangkok).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # สร้างข้อมูลแถวใหม่
            new_row = pd.DataFrame(
                [
                    {
                        "timestamp": current_time,
                        "rank_name": rank_name,
                        "position": position,
                        "department": department,
                        "phone": phone,
                    }
                ]
            )

            # รวมข้อมูลใหม่เข้ากับข้อมูลเดิม
            updated_data = pd.concat(
                [existing_data, new_row], ignore_index=True
            )

            # อัปเดตกลับไปยัง Google Sheets
            conn.update(data=updated_data)

            st.success(
                f"✅ บันทึกข้อมูลเรียบร้อยแล้ว! (เวลาที่บันทึก: {current_time})"
            )
            st.balloons()

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")

st.divider()

# ---------------------------------------------------------
# 5. ส่วนที่ 3: สรุปข้อมูลแบบ Real-Time
# ---------------------------------------------------------
st.subheader("📊 รายงานข้อมูล Real-Time จาก Google Sheets")

try:
    df = conn.read(ttl=0)

    st.metric(label="จำนวนรายการบันทึกทั้งหมด", value=f"{len(df)} รายการ")

    if not df.empty:
        # ซ่อนคอลัมน์ Index (0, 1, 2, ...) ออกจากหน้าจอ
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

except Exception as e:
    st.warning("ไม่สามารถโหลดข้อมูล Real-time ได้ในขณะนี้")
# ---------------------------------------------------------
# 6. ส่วนที่ 4: ตรวจสอบผู้ที่ยังไม่ได้บันทึกข้อมูล (Comparison Report)
# ---------------------------------------------------------
st.divider()
st.subheader("🔍 ตรวจสอบรายชื่อผู้ที่ยังไม่ได้บันทึกข้อมูล")

try:
    # 1. ดึงข้อมูลผู้ที่บันทึกแล้ว
    df_submitted = conn.read(ttl=0)

    # 2. ดึงรายชื่อบุคลากรทั้งหมดจาก Sheet ชื่อ 'MasterList'
    df_master = conn.read(worksheet="MasterList", ttl=0)

    if not df_master.empty:
        # รายชื่อทั้งหมดที่มีในระบบ
        all_names = set(df_master["rank_name"].dropna().unique())

        # รายชื่อคนที่บันทึกข้อมูลแล้ว
        submitted_names = set()
        if not df_submitted.empty and "rank_name" in df_submitted.columns:
            submitted_names = set(df_submitted["rank_name"].dropna().unique())

        # หาคนยังไม่ได้บันทึก (เอาทั้งหมด ลบ คนที่บันทึกแล้ว)
        pending_names = sorted(list(all_names - submitted_names))

        # แสดงผลสรุปด้วย Metric
        col1, col2, col3 = st.columns(3)
        col1.metric("จำนวนบุคลากรทั้งหมด", f"{len(all_names)} คน")
        col2.metric("บันทึกแล้ว", f"{len(submitted_names)} คน")
        col3.metric(
            "ยังไม่ได้บันทึก",
            f"{len(pending_names)} คน",
            delta=f"-{len(pending_names)}" if pending_names else "ครบแล้ว 🎉",
        )

        st.progress(
            len(submitted_names) / len(all_names) if len(all_names) > 0 else 0
        )

        # แสดงตารางรายชื่อผู้ที่ยังไม่ได้บันทึก
        if pending_names:
            st.warning("⚠️ **รายชื่อผู้ที่ยังไม่ได้บันทึกข้อมูล:**")
            df_pending = pd.DataFrame(
                {"ลำดับ": range(1, len(pending_names) + 1), "ยศ ชื่อ - สกุล": pending_names}
            )
            st.dataframe(df_pending, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 บุคลากรทุกคนบันทึกข้อมูลครบถ้วนแล้ว!")

    else:
        st.info(
            "💡 ไม่พบข้อมูลในแผ่นงาน MasterList กรุณาเพิ่มรายชื่อบุคลากรทั้งหมดลงใน Sheet ชื่อ 'MasterList'"
        )

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลเปรียบเทียบ: {e}")
