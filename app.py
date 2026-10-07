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


def send_discord_notify(record_date, shift, rank_name, position, department, phone, timestamp):
    """ฟังก์ชันส่งข้อความแจ้งเตือนเข้า Discord"""
    if (
        not DISCORD_WEBHOOK_URL
        or "https://discord.com/api/webhooks/1557208748081283132/dwrf0Ah8EkESLkrDtZWnR7dZ6Geg0aAuj_S_72u-DmRJ9f0YVEmox-_3M-jjktSqSKSp" in DISCORD_WEBHOOK_URL
    ):
        return  # ข้ามการส่งถ้ายังไม่ได้ตั้งค่า URL

    # จัดรูปแบบข้อความที่จะส่งไปยัง Discord
    payload = {
        "embeds": [
            {
                "title": f"📝 บันทึกข้อมูล WFH ({record_date} - {shift})",
                "color": 3447003,
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
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

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
st.subheader("1. กรอกข้อมูลส่วนตัวและเลือกรอบการปฏิบัติงาน")

# --- เลือกวันที่และรอบการปฏิบัติงาน ---
col_date, col_shift = st.columns(2)

with col_date:
    # สามารถเปลี่ยนรายการวันเป็นวันที่จริงได้ เช่น ["2026-10-07", "2026-10-08", "2026-10-09"]
    date_options = ["วันที่ 12 ต.ค.69", "วันที่ 14 ต.ค.69", "วันที่ 15 ต.ค.69"]
    record_date = st.selectbox("📅 เลือกวันที่ปฏิบัติงานที่บ้าน", options=date_options)

with col_shift:
    shift_options = ["รอบเช้า (08:00 - 08:15)", "รอบบ่าย (13:00 - 13:15)"]
    shift = st.selectbox("⏰ เลือกรอบการบันทึก", options=shift_options)

st.write("---")
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
    st.write("กรุณาตรวจสอบความถูกต้องของข้อมูลที่ท่านกรอกก่อนกดปุ่มยืนยัน")

# ปุ่มกด Submit ยืนยันบันทึกข้อมูล
if st.button("🚀 ยืนยันส่งข้อมูล (Submit)", type="primary"):
    if not (rank_name and position and department and phone):
        st.error("⚠️ กรุณาตรวจสอบความถูกต้องของข้อมูลที่ท่านกรอกก่อนกดปุ่มยืนยัน!")
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

           # บันทึกข้อมูลโดยเพิ่มคอลัมน์ record_date และ shift
            new_row = pd.DataFrame(
                [
                    {
                        "timestamp": current_time,
                        "record_date": record_date,
                        "shift": shift,
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
            
            # แจ้งเตือนเข้า Discord
            send_discord_notify(
                record_date,
                shift,
                rank_name,
                position,
                department,
                phone,
                current_time,
            )

            st.success(
                f"✅ บันทึกข้อมูลเรียบร้อยแล้ว! ({record_date} - {shift})"
            )
            st.balloons()

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")

st.divider()

# ---------------------------------------------------------
# 5. ส่วนที่ 3: สรุปข้อมูลแบบ Real-Time
# ---------------------------------------------------------
st.subheader("📊 รายงานข้อมูลการบันทึก WFH")

try:
    df = conn.read(ttl=0)

    if not df.empty:
        # ตัวกรองข้อมูลบน Dashboard
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_filter_date = st.selectbox(
                "กรองตามวันที่", options=["ทั้งหมด"] + date_options
            )
        with filter_col2:
            selected_filter_shift = st.selectbox(
                "กรองตามรอบ", options=["ทั้งหมด"] + shift_options
            )

        # กรอง DataFrame ตามเงื่อนไขที่เลือก
        filtered_df = df.copy()
        if selected_filter_date != "ทั้งหมด":
            filtered_df = filtered_df[
                filtered_df["record_date"] == selected_filter_date
            ]
        if selected_filter_shift != "ทั้งหมด":
            filtered_df = filtered_df[
                filtered_df["shift"] == selected_filter_shift
            ]

        st.metric(
            label=f"จำนวนรายการบันทึก ({selected_filter_date} | {selected_filter_shift})",
            value=f"{len(filtered_df)} รายการ",
        )

        filtered_df.index = range(1, len(filtered_df) + 1)
        st.dataframe(filtered_df, use_container_width=True)

    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

except Exception as e:
    st.warning("ไม่สามารถโหลดข้อมูล Real-time ได้ในขณะนี้")
# ---------------------------------------------------------
# 6. ส่วนที่ 4: ตรวจสอบรายชื่อผู้ที่ยังไม่ได้บันทึกข้อมูล (แยกรายรอบ)
# ---------------------------------------------------------
st.subheader("🔍 ตรวจสอบรายชื่อผู้ที่ยังไม่ได้บันทึกข้อมูล (แยกตามรอบ)")

# ตัวเลือกรอบวันที่และรอบเวลาที่ต้องการตรวจสอบ
chk_col1, chk_col2 = st.columns(2)
with chk_col1:
    check_date = st.selectbox("เลือกวันที่ต้องการตรวจ", options=date_options, key="chk_d")
with chk_col2:
    check_shift = st.selectbox("เลือกรอบที่ต้องการตรวจ", options=shift_options, key="chk_s")

try:
    # 1. ดึงข้อมูลรายชื่อบุคลากรทั้งหมดจาก Sheet ชื่อ 'MasterList' (ถ้ามี)
    try:
        df_master = conn.read(worksheet="MasterList", ttl=0)
        master_names = df_master["rank_name"].dropna().str.strip().tolist()
    except Exception:
        # รายชื่อสำรอง กรณีที่ยังไม่ได้สร้าง Sheet 'MasterList'
        master_names = [
            "ร.อ. สมชาย ใจดี",
            "ร.ท. สมศักดิ์ มีสุข",
            "ร.ต. หญิง สุชาดา รักดี",
            "พ.อ.อ. วิชัย มั่นคง",
            "จ.อ. พงษ์สิทธิ์ มีมงคล",
        ]

    all_master_set = set(master_names)

    # 2. ดึงข้อมูลผู้บันทึกจาก Sheets
    df_records = conn.read(ttl=0)

    submitted_set = set()
    if not df_records.empty and "rank_name" in df_records.columns:
        # กรองเอาเฉพาะข้อมูลตรงกับวันที่และรอบที่เลือกตรวจ
        matched_records = df_records[
            (df_records["record_date"] == check_date)
            & (df_records["shift"] == check_shift)
        ]
        submitted_set = set(
            matched_records["rank_name"].dropna().str.strip().unique()
        )

    # 3. คำนวณรายชื่อที่ยังไม่ได้บันทึก
    pending_names = sorted(list(all_master_set - submitted_set))

    # แสดงผลสถิติภาพรวม
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("บุคลากรทั้งหมด", f"{len(all_master_set)} คน")
    col_m2.metric("บันทึกแล้ว", f"{len(submitted_set)} คน")
    col_m3.metric(
        "ยังไม่ได้บันทึก",
        f"{len(pending_names)} คน",
        delta=f"-{len(pending_names)}" if pending_names else "ครบแล้ว 🎉",
    )

    # Progress bar ความคืบหน้า
    progress_val = (
        len(submitted_set) / len(all_master_set) if all_master_set else 0.0
    )
    st.progress(min(progress_val, 1.0))

    # แสดงตารางรายชื่อผู้ที่ยังไม่ได้บันทึก
    if pending_names:
        st.warning(
            f"⚠️ **รายชื่อผู้ยังไม่ได้บันทึกข้อมูล ({check_date} | {check_shift}):**"
        )
        df_pending = pd.DataFrame(
            {
                "ลำดับ": range(1, len(pending_names) + 1),
                "ยศ ชื่อ - สกุล": pending_names,
            }
        )
        st.dataframe(df_pending, use_container_width=True, hide_index=True)
    else:
        st.success(
            f"🎉 บุคลากรทุกคนบันทึกข้อมูลประจำ ({check_date} | {check_shift}) ครบถ้วนแล้ว!"
        )

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการตรวจสอบรายชื่อ: {e}")
