import datetime
import re
import pandas as pd
import pytz
import requests
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# ตั้งค่า Discord Webhook URL
# ---------------------------------------------------------
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1557208748081283132/dwrf0Ah8EkESLkrDtZWnR7dZ6Geg0aAuj_S_72u-DmRJ9f0YVEmox-_3M-jjktSqSKSp"


def send_discord_notify(
    record_date, shift, rank_name, position, department, phone, timestamp
):
    """ฟังก์ชันส่งข้อความแจ้งเตือนเข้า Discord พร้อมระบบแจ้งเตือนสถานะ"""
    # 1. เช็กว่าตั้งค่า URL หรือยัง (เช็กกรณีค่าว่าง หรือผู้ใช้ลืมใส่ Webhook จริง)
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL.strip() == "":
        st.warning("⚠️ ยังไม่ได้กำหนด Discord Webhook URL")
        return

    # จัดรูปแบบข้อความที่จะส่งไปยัง Discord
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

        # ตรวจสอบว่า Discord ได้รับข้อความหรือไม่ (HTTP Status 200 หรือ 204 คือสำเร็จ)
        if response.status_code in [200, 204]:
            st.toast("🔔 ส่งการแจ้งเตือนเข้า Discord เรียบร้อยแล้ว!", icon="💬")
        else:
            st.error(
                f"❌ ไม่สามารถส่งข้อความเข้า Discord ได้ (Status Code: {response.status_code})\nรายละเอียด: {response.text}"
            )

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ Discord: {e}")


# ---------------------------------------------------------
# 1. ตั้งค่าหน้าตาของแอป
# ---------------------------------------------------------
st.set_page_config(
    page_title="ระบบบันทึกข้อมูลบุคลากร รร.สธ.ทอ.",
    page_icon="📝",
    layout="centered",
)

# ---------------------------------------------------------
# 2. ส่วนหัวเรื่อง
# ---------------------------------------------------------
st.title(
    "📝 ระบบบันทึกข้อมูลผู้ที่ปฏิบัติงานที่บ้าน (Work From Home) รร.สธ.ทอ.ยศ.ทอ."
)
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

# --- ส่วนสังกัด ---
dept_options = [
    "-- กรุณาเลือกสังกัด --",
    "กกศ.รร.สธ.ทอ.ยศ.ทอ.",
    "กทสธ.รร.สธ.ทอ.ยศ.ทอ.",
    "กนท.รร.สธ.ทอ.ยศ.ทอ.",
    "ผธก.รร.สธ.ทอ.ยศ.ทอ.",
    "ผวผ.รร.สธ.ทอ.ยศ.ทอ.",
]

selected_dept = st.selectbox("สังกัด", options=dept_options)
department = "" if selected_dept == "-- กรุณาเลือกสังกัด --" else selected_dept

# รับค่าเบอร์โทรศัพท์
phone_raw = st.text_input(
    "หมายเลขโทรศัพท์ที่ติดต่อได้", placeholder="เช่น 0812345678", max_chars=10
)

phone_clean = re.sub(r"\D", "", phone_raw)

if len(phone_clean) == 10:
    phone = re.sub(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", phone_clean)
    st.caption(f"📱 เบอร์โทรศัพท์ที่บันทึก: **{phone}**")
else:
    phone = phone_clean
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
        st.error(
            "⚠️ กรุณาตรวจสอบความถูกต้องของข้อมูลที่ท่านกรอกก่อนกดปุ่มยืนยัน!"
        )
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

            # บันทึกข้อมูล
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

            updated_data = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(data=updated_data)

            st.success(
                f"✅ บันทึกข้อมูลเรียบร้อยแล้ว! ({record_date} - {shift})"
            )
            st.balloons()

            # --- เรียกส่งข้อมูลไปยัง Discord ---
            send_discord_notify(
                record_date,
                shift,
                rank_name,
                position,
                department,
                phone,
                current_time,
            )

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
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_filter_date = st.selectbox(
                "กรองตามวันที่", options=["ทั้งหมด"] + date_options
            )
        with filter_col2:
            selected_filter_shift = st.selectbox(
                "กรองตามรอบ", options=["ทั้งหมด"] + shift_options
            )

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

chk_col1, chk_col2 = st.columns(2)
with chk_col1:
    check_date = st.selectbox(
        "เลือกวันที่ต้องการตรวจ", options=date_options, key="chk_d"
    )
with chk_col2:
    check_shift = st.selectbox(
        "เลือกรอบที่ต้องการตรวจ", options=shift_options, key="chk_s"
    )

try:
    try:
        df_master = conn.read(worksheet="MasterList", ttl=0)
        master_names = df_master["rank_name"].dropna().str.strip().tolist()
    except Exception:
        master_names = [
            "ร.อ. สมชาย ใจดี",
            "ร.ท. สมศักดิ์ มีสุข",
            "ร.ต. หญิง สุชาดา รักดี",
            "พ.อ.อ. วิชัย มั่นคง",
            "จ.อ. พงษ์สิทธิ์ มีมงคล",
        ]

    all_master_set = set(master_names)
    df_records = conn.read(ttl=0)

    submitted_set = set()
    if not df_records.empty and "rank_name" in df_records.columns:
        matched_records = df_records[
            (df_records["record_date"] == check_date)
            & (df_records["shift"] == check_shift)
        ]
        submitted_set = set(
            matched_records["rank_name"].dropna().str.strip().unique()
        )

    pending_names = sorted(list(all_master_set - submitted_set))

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("บุคลากรทั้งหมด", f"{len(all_master_set)} คน")
    col_m2.metric("บันทึกแล้ว", f"{len(submitted_set)} คน")
    col_m3.metric(
        "ยังไม่ได้บันทึก",
        f"{len(pending_names)} คน",
        delta=f"-{len(pending_names)}" if pending_names else "ครบแล้ว 🎉",
    )

    progress_val = (
        len(submitted_set) / len(all_master_set) if all_master_set else 0.0
    )
    st.progress(min(progress_val, 1.0))

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
