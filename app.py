import datetime
import pandas as pd
import streamlit as st

# ตั้งค่าหน้าตาของแอปสำหรับรองรับมือถือ
st.set_page_config(
    page_title="ระบบบันทึกข้อมูลบุคลากร", page_icon="📝", layout="centered"
)

st.title("📝 ระบบบันทึกข้อมูลบุคลากร")
st.caption("กรอกข้อมูลเพื่อบันทึกเข้าระบบออนไลน์")

# สร้าง/โหลด Session State สำหรับจำลอง Database (หรือเชื่อม Google Sheets)
if "database" not in st.session_state:
    st.session_state.database = pd.DataFrame(
        columns=[
            "วัน-เวลา บันทึก",
            "ยศ ชื่อ - สกุล",
            "ตำแหน่ง",
            "สังกัด",
            "เบอร์โทรศัพท์",
        ]
    )

# --- ส่วนที่ 1: ฟอร์มกรอกข้อมูล ---
st.subheader("1. กรอกข้อมูลส่วนตัว")

rank_name = st.text_input(
    "ยศ ชื่อ - สกุล", placeholder="เช่น ร.อ. สมชาย ใจดี"
)
position = st.text_input("ตำแหน่ง", placeholder="เช่น ผบ.ร้อย.")
department = st.text_input("สังกัด", placeholder="เช่น นทพ.")
phone = st.text_input(
    "หมายเลขโทรศัพท์ที่ติดต่อได้", placeholder="เช่น 0812345678"
)

st.divider()

# --- ส่วนที่ 2: ตรวจสอบข้อมูลก่อนส่ง (Confirm Step) ---
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
    # ตรวจสอบการกรอกข้อมูลให้ครบถ้วน
    if not (rank_name and position and department and phone):
        st.error("⚠️ กรุณากรอกข้อมูลให้ครบทุกช่องก่อนกดยืนยัน!")
    else:
        # บันทึกเวลาอัตโนมัติ (Timestamp)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # สร้าง Record ใหม่
        new_data = {
            "วัน-เวลา บันทึก": current_time,
            "ยศ ชื่อ - สกุล": rank_name,
            "ตำแหน่ง": position,
            "สังกัด": department,
            "เบอร์โทรศัพท์": phone,
        }

        # บันทึกลงระบบ
        st.session_state.database = pd.concat(
            [st.session_state.database, pd.DataFrame([new_data])],
            ignore_index=True,
        )

        st.success("✅ บันทึกข้อมูลสำเร็จเรียบร้อยแล้ว!")
        st.balloons()

st.divider()

# --- ส่วนที่ 3: สรุปข้อมูลแบบ Real-Time & ส่งออกเป็น Excel ---
st.subheader("📊 รายงานข้อมูล Real-Time")

df = st.session_state.database

# แสดงจำนวนข้อมูลทั้งหมด
st.metric(label="จำนวนรายการบันทึกทั้งหมด", value=f"{len(df)} รายการ")

if not df.empty:
    # แสดงตารางข้อมูล Real-Time
    st.dataframe(df, use_container_width=True)

    # ปุ่มดาวน์โหลดไฟล์ Excel / CSV
    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 ดาวน์โหลดข้อมูลเป็นไฟล์ Excel/CSV",
        data=csv_data,
        file_name=f"personnel_records_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
