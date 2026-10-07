import datetime
import re
import pandas as pd
import pytz  # ไลบรารีสำหรับจัดการ Time Zone
import streamlit as st
from streamlit_gsheets import GSheetsConnection

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
department = st.text_input(
    "สังกัด", placeholder="เช่น กกศ., กทสธ., กนท., ผธก., ผวผ."
)

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
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลในระบบ")

except Exception as e:
    st.warning("ไม่สามารถโหลดข้อมูล Real-time ได้ในขณะนี้")
