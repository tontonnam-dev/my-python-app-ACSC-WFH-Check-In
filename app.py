import datetime
import pandas as pd
import pytz
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ตั้งค่าหน้าตาของแอป
st.set_page_config(
    page_title="ระบบบันทึกข้อมูลข้าราชการที่ปฏิบัติงานที่บ้าน (Work From Home) หน่วย รร.สธ.ทอ.ยศ.ทอ.", page_icon="📝", layout="centered"
)

# ==========================================
# 🖼️ ตั้งค่าโลโก้ (ใส่ชื่อไฟล์ หรือ URL รูปภาพ)
# ==========================================
LOGO_URL_OR_PATH = "logo.png"  # หรือ "https://your-website.com/logo.png"

# แสดงผลโลโก้และชื่อแอป
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image(LOGO_URL_OR_PATH, width=80)
    except Exception:
        st.write("🏛️")  # ไอคอนสำรองกรณีไม่มีไฟล์รูป

with col_title:
    st.title("ระบบบันทึกข้อมูลข้าราชการที่ปฏิบัติงานที่บ้าน (Work From Home) หน่วย รร.สธ.ทอ.ยศ.ทอ.")

st.caption("เชื่อมต่อข้อมูลตรงกับ Google Sheets (เวลาประเทศไทย UTC+7)")

# เชื่อมต่อกับ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ส่วนที่ 1: ฟอร์มกรอกข้อมูล ---
st.subheader("1. กรอกข้อมูลส่วนตัว")

rank_name = st.text_input(
    "ยศ ชื่อ - สกุล", placeholder="เช่น ร.อ. สมชาย ใจดี"
)
position = st.text_input("ตำแหน่ง", placeholder="เช่น ผอ.กอง, รอง ผอ.กอง, หน.ผธก. เป็นต้น")
department = st.text_input("สังกัด", placeholder="เช่น กกศ., กทสธ., กนท., ผธก., ผวผ. เป็นต้น")
phone = st.text_input(
    "หมายเลขโทรศัพท์ที่ติดต่อได้", placeholder="เช่น 0812345678"
)

st.divider()

# --- ส่วนที่ 2: ตรวจสอบข้อมูลก่อนส่ง ---
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
    st.write("กรุณากรอกข้อมูลในฟอร์มข้างต้น")

# ปุ่มกด Submit ยืนยันบันทึกข้อมูล
if st.button("🚀 ยืนยันส่งข้อมูล (Submit)", type="primary"):
    if not (rank_name and position and department and phone):
        st.error("⚠️ กรุณากรอกข้อมูลให้ครบทุกช่องและตรวจสอบข้อมูลก่อนกดยืนยัน!")
    else:
        try:
            existing_data = conn.read(ttl=0)

            # เวลาประเทศไทย UTC+7
            tz_bangkok = pytz.timezone("Asia/Bangkok")
            current_time = datetime.datetime.now(tz_bangkok).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

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

            updated_data = pd.concat(
                [existing_data, new_row], ignore_index=True
            )
            conn.update(data=updated_data)

            st.success(
                f"✅ บันทึกข้อมูลเรียบร้อยแล้ว! (เวลาที่บันทึก: {current_time})"
            )
            st.balloons()

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")

st.divider()

# --- ส่วนที่ 3: สรุปข้อมูลแบบ Real-Time ---
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
