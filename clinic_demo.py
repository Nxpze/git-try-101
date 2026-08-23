from datetime import datetime, timedelta, date
import random
import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def parse_date(date_str):
    """แปลงข้อความวันที่ (YYYY-MM-DD หรือ YYYY/MM/DD หรือ DD/MM/YYYY) เป็น date object"""
    if isinstance(date_str, (datetime, date)):
        return date_str if isinstance(date_str, date) else date_str.date()

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: '{date_str}' (กรุณาใช้ YYYY-MM-DD หรือ YYYY/MM/DD)")


def age_calculator(dob):
    """คำนวณอายุจากวันเกิด"""
    birthdate = parse_date(dob)
    today = datetime.today().date()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age


# ---------------------------------------------------------
# Entity Classes (Crow's Foot Diagram)
# ---------------------------------------------------------
class Patient:
    """
    PATIENT Entity
    - P_id (PK): string
    - fullname: string
    - dob: date
    - phone_number: string
    - allergies: string
    - underlying_disease: string
    """
    def __init__(self, patient_id, fullname, dob, phone_number, allergies="ไม่มี", underlying_disease="ไม่มี"):
        self.p_id = str(patient_id)
        self.Patient_id = self.p_id  # รองรับการเรียกแบบเดิม
        self.fullname = fullname
        self.dob = str(dob)
        self.phone_number = phone_number
        self.allergies = allergies
        self.underlying_disease = underlying_disease
        self.age = self.age_cal()

    def age_cal(self):
        return age_calculator(self.dob)

    def is_adult(self):
        return self.age >= 20

    def to_dict(self):
        return {
            "p_id": self.p_id,
            "fullname": self.fullname,
            "dob": self.dob,
            "age": self.age,
            "phone_number": self.phone_number,
            "allergies": self.allergies,
            "underlying_disease": self.underlying_disease,
            "adult_status": "บรรลุนิติภาวะ" if self.is_adult() else "ยังไม่บรรลุนิติภาวะ",
        }

    def __repr__(self):
        return f"<Patient {self.p_id}: {self.fullname}, อายุ {self.age} ปี, แพ้ยา: {self.allergies}>"


class Queue:
    """
    QUEUE Entity
    - queue_id (PK): string
    - P_id (FK): string
    - queue_number: string
    - symptoms: string
    - urgency_level: string (Red, Yellow, Green, White)
    - arrival_time: datetime
    - waiting_time: int
    """
    def __init__(self, queue_id, patient_id, queue_number, symptoms, urgency_level, arrival_time=None):
        self.queue_id = str(queue_id)
        self.p_id = str(patient_id)
        self.Patient_id = self.p_id
        self.Paient_id = self.p_id  # แก้ไข typo ให้ backward-compatible
        self.queue_number = queue_number
        self.symptoms = symptoms
        self.urgency_level = urgency_level  # Red, Yellow, Green, White
        self.arrival_time = arrival_time if arrival_time else datetime.now()

        # ระบบติดตามเวลารอตรวจและการรีเช็คโดยพยาบาล
        self.waiting_time = self.calculate_initial_waiting_time()
        self.alert_status = "รอตามปกติ"  # "รอตามปกติ", "ต้องรีเช็ค", "ดันคิวทันที"
        self.recheck_count = 0
        self.next_check_time = 30  # แจ้งเตือนครั้งแรกที่ 30 นาที

        # ตรวจสอบสถานะการแจ้งเตือนเบื้องต้น
        self.evaluate_alert_status()

    def calculate_initial_waiting_time(self):
        wait_matrix = {"Red": 0, "Yellow": 15, "Green": 45, "White": 60}
        return wait_matrix.get(self.urgency_level, 30)

    def evaluate_alert_status(self):
        # เตือนเมื่อรอครบ 30 นาทีขึ้นไป
        if self.waiting_time >= 30 and self.alert_status != "ดันคิวทันที":
            self.alert_status = "ต้องรีเช็ค"

    def nurse_recheck(self, patient_condition, extension_minutes=30):
        """ฟังก์ชันให้พยาบาลบันทึกผลการรีเช็คอาการ"""
        self.recheck_count += 1
        if patient_condition == "อาการแย่ลง":
            self.fast_track_trigger()
        else:
            self.alert_status = "รอตามปกติ (รีเช็คแล้ว)"
            self.next_check_time += extension_minutes  # ต่อเวลานับถอยหลังอีก 30 หรือ 60 นาที

    def fast_track_trigger(self):
        """ปุ่มลัดอัปเกรดสถานะ: ดันคิวทันทีเมื่ออาการแย่ลง"""
        self.urgency_level = "Red"
        self.alert_status = "ดันคิวทันที"
        self.waiting_time = 0

    def to_dict(self):
        return {
            "queue_id": self.queue_id,
            "p_id": self.p_id,
            "queue_number": self.queue_number,
            "symptoms": self.symptoms,
            "urgency_level": self.urgency_level,
            "arrival_time": self.arrival_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(self.arrival_time, datetime) else str(self.arrival_time),
            "waiting_time": self.waiting_time,
            "alert_status": self.alert_status,
            "recheck_count": self.recheck_count,
        }

    def __repr__(self):
        return f"<Queue {self.queue_number} (ID: {self.queue_id}) | ผู้ป่วย: {self.p_id} | ระดับ: {self.urgency_level} | สถานะ: {self.alert_status}>"


class MedicalRecord:
    """
    MEDICAL_RECORD Entity
    - record_id (PK): string
    - P_id (FK): string
    - D_id (FK): string
    - record_date: date
    - diagnosis: string
    - status: string
    - prescribed_meds: string
    """
    DOCTOR = {
        "DOC001": {
            "doctor_name": "นพ. สมชาย ใจดี",
            "specialization": "อายุรกรรม"
        },
        "DOC002": {
            "doctor_name": "พญ. วิภาดา รักษาดี",
            "specialization": "กุมารเวชศาสตร์ (หมอเด็ก)"
        },
        "DOC003": {
            "doctor_name": "นพ. ธนกฤต เก่งกาจ",
            "specialization": "ศัลยกรรมกระดูกและข้อ"
        }
    }

    def __init__(self, record_id, patient_id, doctor_id, record_date, diagnosis, status, prescribed_meds):
        self.record_id = str(record_id)
        self.p_id = str(patient_id)
        self.Patient_id = self.p_id
        self.d_id = str(doctor_id)
        self.doctor_id = self.d_id

        doctor_info = self.DOCTOR.get(doctor_id, {
            "doctor_name": "ไม่พบข้อมูลแพทย์",
            "specialization": "ไม่ระบุ"
        })

        self.doctor_name = doctor_info.get("doctor_name")
        self.doctor_specialization = doctor_info.get("specialization")
        self.record_date = parse_date(record_date) if isinstance(record_date, str) else record_date
        self.diagnosis = diagnosis
        self.status = status
        self.prescribed_meds = prescribed_meds

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "p_id": self.p_id,
            "d_id": self.d_id,
            "doctor_name": self.doctor_name,
            "doctor_specialization": self.doctor_specialization,
            "record_date": str(self.record_date),
            "diagnosis": self.diagnosis,
            "status": self.status,
            "prescribed_meds": self.prescribed_meds,
        }

    def __repr__(self):
        return f"<MedicalRecord {self.record_id} | ผู้ป่วย: {self.p_id} | แพทย์: {self.doctor_name} | วินิจฉัย: {self.diagnosis}>"


class Bill:
    """
    BILL Entity
    - bill_id (PK): string
    - record_id (FK): string
    - P_id (FK): string
    - treatment_fee: decimal/float
    - medication_fee: decimal/float
    - total_payment: decimal/float
    - status: string
    """
    def __init__(self, bill_id, record_id, patient_id, treatment_fee, medication_fee, status="ยังไม่ชำระ"):
        self.bill_id = str(bill_id)
        self.record_id = str(record_id)
        self.p_id = str(patient_id)
        self.Patient_id = self.p_id
        self.treatment_fee = float(treatment_fee)
        self.medication_fee = float(medication_fee)
        self.total_payment = self.calculate_total_payment()
        self.status = status

    def calculate_total_payment(self):
        return round(self.treatment_fee + self.medication_fee, 2)

    def pay(self):
        """บันทึกการชำระเงิน"""
        self.status = "ชำระเงินเรียบร้อยแล้ว"
        return self.total_payment

    def to_dict(self):
        return {
            "bill_id": self.bill_id,
            "record_id": self.record_id,
            "p_id": self.p_id,
            "treatment_fee": self.treatment_fee,
            "medication_fee": self.medication_fee,
            "total_payment": self.total_payment,
            "status": self.status,
        }

    def __repr__(self):
        return f"<Bill {self.bill_id} | ผู้ป่วย: {self.p_id} | ยอดรวม: {self.total_payment:,.2f} บาท | สถานะ: {self.status}>"


# ---------------------------------------------------------
# Clinic Management System Controller
# ---------------------------------------------------------
class ClinicSystem:
    """ระบบบริหารจัดการคลินิก เชื่อมโยง Patient, Queue, MedicalRecord, Bill ตาม Crow's Foot Diagram"""

    def __init__(self):
        self.patients = {}        # P_id -> Patient
        self.queues = {}          # queue_id -> Queue
        self.medical_records = {} # record_id -> MedicalRecord
        self.bills = {}           # bill_id -> Bill

        # ตัวนับรหัสอัตโนมัติ
        self._patient_counter = 1
        self._queue_counter = 1
        self._record_counter = 1
        self._bill_counter = 1

    # 1. จัดการข้อมูลคนไข้ (PATIENT)
    def register_patient(self, fullname, dob, phone_number, allergies="ไม่มี", underlying_disease="ไม่มี", p_id=None):
        if not p_id:
            p_id = f"P{self._patient_counter:03d}"
            self._patient_counter += 1

        patient = Patient(
            patient_id=p_id,
            fullname=fullname,
            dob=dob,
            phone_number=phone_number,
            allergies=allergies,
            underlying_disease=underlying_disease
        )
        self.patients[patient.p_id] = patient
        return patient

    # 2. ออกคิวและคัดกรองอาการ (QUEUE)
    def create_queue(self, p_id, symptoms, urgency_level="Green", arrival_time=None):
        if p_id not in self.patients:
            raise ValueError(f"ไม่พบข้อมูลคนไข้รหัส: {p_id}")

        queue_id = f"Q{self._queue_counter:03d}"
        prefix = urgency_level[0].upper() if urgency_level else "Q"
        queue_number = f"{prefix}-{self._queue_counter:03d}"
        self._queue_counter += 1

        queue = Queue(
            queue_id=queue_id,
            patient_id=p_id,
            queue_number=queue_number,
            symptoms=symptoms,
            urgency_level=urgency_level,
            arrival_time=arrival_time
        )
        self.queues[queue.queue_id] = queue
        return queue

    # 3. พยาบาลรีเช็คอาการ
    def nurse_recheck_queue(self, queue_id, patient_condition, extension_minutes=30):
        if queue_id not in self.queues:
            raise ValueError(f"ไม่พบคิวรหัส: {queue_id}")

        queue = self.queues[queue_id]
        queue.nurse_recheck(patient_condition, extension_minutes)
        return queue

    # 4. บันทึกผลการตรวจรักษา (MEDICAL_RECORD)
    def create_medical_record(self, p_id, doctor_id, diagnosis, prescribed_meds, status="เสร็จสิ้นการตรวจ", record_date=None):
        if p_id not in self.patients:
            raise ValueError(f"ไม่พบข้อมูลคนไข้รหัส: {p_id}")

        record_id = f"REC{self._record_counter:03d}"
        self._record_counter += 1

        if not record_date:
            record_date = datetime.today().date()

        record = MedicalRecord(
            record_id=record_id,
            patient_id=p_id,
            doctor_id=doctor_id,
            record_date=record_date,
            diagnosis=diagnosis,
            status=status,
            prescribed_meds=prescribed_meds
        )
        self.medical_records[record.record_id] = record
        return record

    # 5. ออกใบเสร็จและการเงิน (BILL)
    def create_bill(self, record_id, treatment_fee, medication_fee, status="ยังไม่ชำระ"):
        if record_id not in self.medical_records:
            raise ValueError(f"ไม่พบประวัติการตรวจรหัส: {record_id}")

        record = self.medical_records[record_id]
        bill_id = f"B{self._bill_counter:03d}"
        self._bill_counter += 1

        bill = Bill(
            bill_id=bill_id,
            record_id=record_id,
            patient_id=record.p_id,
            treatment_fee=treatment_fee,
            medication_fee=medication_fee,
            status=status
        )
        self.bills[bill.bill_id] = bill
        return bill

    def pay_bill(self, bill_id):
        if bill_id not in self.bills:
            raise ValueError(f"ไม่พบใบแจ้งหนี้รหัส: {bill_id}")
        bill = self.bills[bill_id]
        bill.pay()
        return bill

    # 6. ค้นหาประวัติคนไข้แบบองค์รวม (Patient History View)
    def get_patient_summary(self, p_id):
        patient = self.patients.get(p_id)
        if not patient:
            return None

        p_queues = [q for q in self.queues.values() if q.p_id == p_id]
        p_records = [r for r in self.medical_records.values() if r.p_id == p_id]
        p_bills = [b for b in self.bills.values() if b.p_id == p_id]

        return {
            "patient": patient,
            "queues": p_queues,
            "medical_records": p_records,
            "bills": p_bills
        }

    # 7. สรุปรายงานข้อมูลด้วย pandas
    def get_dataframes(self):
        df_patients = pd.DataFrame([p.to_dict() for p in self.patients.values()])
        df_queues = pd.DataFrame([q.to_dict() for q in self.queues.values()])
        df_records = pd.DataFrame([r.to_dict() for r in self.medical_records.values()])
        df_bills = pd.DataFrame([b.to_dict() for b in self.bills.values()])
        return df_patients, df_queues, df_records, df_bills

    
    def load_patients_from_dataframe(self, df):
        """โหลดข้อมูลคนไข้จำนวนมากจาก Pandas DataFrame เข้าระบบ"""
        count = 0
        for _, row in df.iterrows():
            self.register_patient(
                fullname=row.get("fullname"),
                dob=str(row.get("dob")),
                phone_number=str(row.get("phone_number")),
                allergies=row.get("allergies", "ไม่มี"),
                underlying_disease=row.get("underlying_disease", "ไม่มี"),
                p_id=str(row.get("p_id")) if pd.notna(row.get("p_id")) else None
            )
            count += 1
        print(f"✅ โหลดข้อมูลคนไข้จาก DataFrame สำเร็จทั้งหมด {count} รายการ")
    def load_patients_from_csv(self, file_path):
        """อ่านไฟล์ CSV และโหลดข้อมูลคนไข้เข้าสู่ระบบอัตโนมัติ"""
        df = pd.read_csv(file_path)
        self.load_patients_from_dataframe(df)

# ---------------------------------------------------------
# Demonstration Workflow & Interactive Console
# ---------------------------------------------------------
def run_demo_simulation():
    """ฟังก์ชันจำลองกระบวนการทำงานทั้งระบบคลินิกตามแผนผัง Flowchart และ Crow's Foot Diagram"""
    print("\n" + "=" * 65)
    print("🏥 เริ่มต้นการทำงานจำลองระบบคลินิก (End-to-End Simulation)")
    print("=" * 65)

    clinic = ClinicSystem()

    # 1. ลงทะเบียนผู้ป่วยตัวอย่าง
    print("\n--- 1. ลงทะเบียนผู้ป่วย (PATIENT Registration) ---")
    p1 = clinic.register_patient(
        fullname="นายสมศักดิ์ รักสงบ",
        dob="1995-04-12",
        phone_number="081-234-5678",
        allergies="แพ้ยา Penicillin",
        underlying_disease="ความดันโลหิตสูง"
    )
    p2 = clinic.register_patient(
        fullname="ด.ญ. มะลิ สดใส",
        dob="2018-09-25",
        phone_number="089-987-6543",
        allergies="ไม่มี",
        underlying_disease="หอบหืด"
    )
    p3 = clinic.register_patient(
        fullname="นายวิชัย ชัยชนะ",
        dob="1980-01-15",
        phone_number="086-555-1234",
        allergies="ไม่มี",
        underlying_disease="เบาหวาน"
    )

    for p in clinic.patients.values():
        status_text = "บรรลุนิติภาวะแล้ว" if p.is_adult() else "ยังไม่บรรลุนิติภาวะ"
        print(f"✅ ลงทะเบียน: [{p.p_id}] {p.fullname} | วันเกิด: {p.dob} (อายุ {p.age} ปี - {status_text}) | แพ้ยา: {p.allergies}")

    # 2. คัดกรองและออกคิว (Triage & QUEUE)
    print("\n--- 2. คัดกรองอาการและออกคิวตรวจ (Triage & QUEUE Creation) ---")
    q1 = clinic.create_queue(p1.p_id, symptoms="มีไข้สูง ปวดศีรษะ เจ็บคอ", urgency_level="Yellow")
    q2 = clinic.create_queue(p2.p_id, symptoms="ไอ หอบ หายใจมีเสียงหวีด", urgency_level="Red")
    q3 = clinic.create_queue(p3.p_id, symptoms="ปวดข้อเข่าเรื้อรัง มาตรวจตามนัด", urgency_level="White")

    for q in clinic.queues.values():
        print(f"🎫 คิว: {q.queue_number} (รหัส {q.queue_id}) -> ผู้ป่วย {q.p_id} | ระดับความเร่งด่วน: {q.urgency_level} | เวลารอประมาณ: {q.waiting_time} นาที | สถานะ: {q.alert_status}")

    # 3. พยาบาลรีเช็คอาการ (Nurse Recheck)
    print("\n--- 3. การติดตามและรีเช็คอาการโดยพยาบาล (Nurse Recheck Workflow) ---")
    print(f"👩‍⚕️ พยาบาลตรวจสอบคิว {q1.queue_number} (นายสมศักดิ์): คนไข้ยังคงมีไข้ แต่ทรงตัว")
    clinic.nurse_recheck_queue(q1.queue_id, patient_condition="อาการทรงตัว", extension_minutes=30)
    print(f"   -> สถานะคิว {q1.queue_number} อัปเดตเป็น: {q1.alert_status} (เวลารีเช็คครั้งถัดไปใน {q1.next_check_time} นาที)")

    print(f"👩‍⚕️ พยาบาลตรวจสอบคิว {q3.queue_number} (นายวิชัย): มีอาการแน่นหน้าอกเฉียบพลัน (อาการแย่ลง!)")
    clinic.nurse_recheck_queue(q3.queue_id, patient_condition="อาการแย่ลง")
    print(f"   -> [Fast-Track Triggered!] สถานะคิว {q3.queue_number} ถูกอัปเกรดเป็น: ระดับ {q3.urgency_level} | สถานะ: {q3.alert_status} | เวลารอ: {q3.waiting_time} นาที")

    # 4. พบแพทย์และบันทึกประวัติการรักษา (Doctor Examination & MEDICAL_RECORD)
    print("\n--- 4. ตรวจรักษาและบันทึกเวชระเบียน (Doctor Exam & MEDICAL_RECORD) ---")
    rec1 = clinic.create_medical_record(
        p_id=p1.p_id,
        doctor_id="DOC001",
        diagnosis="ไข้หวัดใหญ่สายพันธุ์ A (Influenza A)",
        prescribed_meds="Oseltamivir 75mg, Paracetamol 500mg (หลีกเลี่ยงกลุ่ม Penicillin)"
    )
    rec2 = clinic.create_medical_record(
        p_id=p2.p_id,
        doctor_id="DOC002",
        diagnosis="โรคหอบหืดกำเริบเฉียบพลัน (Acute Asthma Attack)",
        prescribed_meds="Salbutamol Nebulizer, Prednisolone Syrup"
    )
    rec3 = clinic.create_medical_record(
        p_id=p3.p_id,
        doctor_id="DOC003",
        diagnosis="ข้อเข่าเสื่อมระยะที่ 2 และภาวะขาดเลือดชั่วคราว (Refer ฉุกเฉิน)",
        prescribed_meds="Glucosamine, ยาคลายกล้ามเนื้อ, ส่งต่อแพทย์หัวใจ"
    )

    for rec in clinic.medical_records.values():
        print(f"📋 เวชระเบียน [{rec.record_id}] ผู้ป่วย {rec.p_id} | แพทย์: {rec.doctor_name} ({rec.doctor_specialization})")
        print(f"   การวินิจฉัย: {rec.diagnosis} | ยาที่สั่ง: {rec.prescribed_meds}")

    # 5. คิดเงินและออกใบเสร็จ (Billing & BILL)
    print("\n--- 5. คิดเงินและชำระค่าบริการ (BILL Generation & Settlement) ---")
    b1 = clinic.create_bill(rec1.record_id, treatment_fee=300.0, medication_fee=450.0)
    b2 = clinic.create_bill(rec2.record_id, treatment_fee=500.0, medication_fee=620.0)
    b3 = clinic.create_bill(rec3.record_id, treatment_fee=800.0, medication_fee=1250.0)

    for b in clinic.bills.values():
        print(f"💳 ใบแจ้งหนี้ [{b.bill_id}] สำหรับเวชระเบียน {b.record_id} (ผู้ป่วย {b.p_id}) | ค่าตรวจ: {b.treatment_fee:,.2f} | ค่ายา: {b.medication_fee:,.2f} | รวม: {b.total_payment:,.2f} บาท [{b.status}]")

    print("\n💰 ชำระเงินสำหรับใบเสร็จ B001 และ B002:")
    clinic.pay_bill(b1.bill_id)
    clinic.pay_bill(b2.bill_id)
    print(f"   -> [{b1.bill_id}] สถานะ: {b1.status}")
    print(f"   -> [{b2.bill_id}] สถานะ: {b2.status}")
    print(f"   -> [{b3.bill_id}] สถานะ: {b3.status}")

    # 6. สรุปประวัติผู้ป่วยรายบุคคล
    print("\n" + "=" * 65)
    print(f"🔍 สรุปประวัติครบวงจรของผู้ป่วย {p1.fullname} ({p1.p_id})")
    print("=" * 65)
    summary = clinic.get_patient_summary(p1.p_id)
    print(f"👤 ข้อมูลทั่วไป: {summary['patient']}")
    print(f"🎫 ประวัติการรับคิว: {summary['queues']}")
    print(f"📋 ประวัติการตรวจ: {summary['medical_records']}")
    print(f"💳 ประวัติการชำระเงิน: {summary['bills']}")

    # 7. สรุปรายงานตาราง Pandas DataFrame
    print("\n" + "=" * 65)
    print("📊 สรุปรายงานข้อมูลคลินิก (Pandas Summary Table)")
    print("=" * 65)
    df_p, df_q, df_r, df_b = clinic.get_dataframes()
    print("\n[ ตารางเวชระเบียนและการรักษา ]")
    print(df_r[["record_id", "p_id", "doctor_name", "diagnosis", "status"]].to_string(index=False))

    print("\n[ ตารางสรุปการเงินและใบเสร็จ ]")
    print(df_b[["bill_id", "record_id", "p_id", "total_payment", "status"]].to_string(index=False))

    total_revenue = df_b[df_b["status"] == "ชำระเงินเรียบร้อยแล้ว"]["total_payment"].sum()
    pending_revenue = df_b[df_b["status"] != "ชำระเงินเรียบร้อยแล้ว"]["total_payment"].sum()
    print(f"\n💵 รายรับที่ชำระแล้ว: {total_revenue:,.2f} บาท | ยอดค้างชำระ: {pending_revenue:,.2f} บาท")
    print("=" * 65 + "\n")
    return clinic


def interactive_patient_entry(clinic=None):
    """
    โหมดบริการคนไข้แบบครบวงจร (Full Clinical Workflow):
    1. ตรวจสอบคนไข้เก่า/ลงทะเบียนคนไข้ใหม่
    2. คัดกรองอาการและออกบัตรคิว (Triage & Queue)
    3. แพทย์ตรวจรักษา บันทึกการวินิจฉัย (Diagnosis), สถานะ (Status), รายการยา (Prescribed Meds)
    4. ออกใบนัดหมายแพทย์ (Appointment Slip) ที่มี Patient_id, fullname, doctor_name, phone_num, วันที่นัด
    5. คิดเงิน ออกบิลคำนวณ total_payment (ค่าตรวจ + ค่ายา) และบันทึกข้อมูลทุกอย่างลงระบบ
    """
    print("\n" + "=" * 65)
    print("🏥 ระบบงานบริการคนไข้ครบวงจร (Full Clinic Workflow System)")
    print("=" * 65)

    if clinic is None:
        clinic = ClinicSystem()

    try:
        # ============================================================
        # 1. ตรวจสอบคนไข้เดิม หรือ ลงทะเบียนคนไข้ใหม่
        # ============================================================
        print("\n--- [ขั้นตอนที่ 1] ค้นหาประวัติ / ลงทะเบียนคนไข้ ---")
        patient_id = input("กรุณากรอกรหัสประจำตัวคนไข้ (P_id) [ถ้าคนไข้ใหม่กด Enter ข้าม]: ").strip()

        if patient_id and patient_id in clinic.patients:
            # --- [กรณีพบคนไข้เก่า] ---
            patient = clinic.patients[patient_id]
            status_adult = "บรรลุนิติภาวะแล้ว" if patient.is_adult() else "ยังไม่บรรลุนิติภาวะ"
            print(f"\n✅ [พบข้อมูลในระบบ] รหัส: {patient.p_id} | คุณ{patient.fullname}")
            print(f"   วันเกิด: {patient.dob} (อายุ {patient.age} ปี - {status_adult})")
            print(f"   เบอร์โทรศัพท์: {patient.phone_number}")
            print(f"   ⚠️ ประวัติแพ้ยา: {patient.allergies} | โรคประจำตัว: {patient.underlying_disease}")
            print("   -> ข้ามขั้นตอนลงทะเบียน ไปยังการซักถามอาการทันที")
        else:
            # --- [กรณีคนไข้ใหม่] ---
            if patient_id:
                print(f"\n❌ ไม่พบรหัส '{patient_id}' ในระบบ -> เข้าสู่ขั้นตอนลงทะเบียนคนไข้ใหม่")
            else:
                print("\n📝 เข้าสู่ขั้นตอนลงทะเบียนคนไข้ใหม่")

            fullname = input("กรุณากรอกชื่อ-นามสกุลคนไข้: ").strip()
            while not fullname:
                fullname = input("กรุณากรอกชื่อคนไข้ (ห้ามเว้นว่าง): ").strip()

            dob = input("กรุณากรอกวันเกิด (YYYY-MM-DD หรือ YYYY/MM/DD): ").strip()
            phone = input("กรุณากรอกเบอร์โทรศัพท์: ").strip()
            allergies = input("ประวัติการแพ้ยา (ถ้าไม่มีกด Enter): ").strip() or "ไม่มี"
            disease = input("โรคประจำตัว (ถ้าไม่มีกด Enter): ").strip() or "ไม่มี"

            patient = clinic.register_patient(
                fullname=fullname,
                dob=dob,
                phone_number=phone,
                allergies=allergies,
                underlying_disease=disease,
                p_id=patient_id if patient_id else None
            )

            status_adult = "บรรลุนิติภาวะแล้ว" if patient.is_adult() else "ยังไม่บรรลุนิติภาวะ"
            print(f"\n✅ ลงทะเบียนสำเร็จ! รหัสผู้ป่วย: [{patient.p_id}] คุณ{patient.fullname} (อายุ {patient.age} ปี - {status_adult})")

        # ============================================================
        # 2. ซักถามอาการและออกบัตรคิว (Triage & Queue)
        # ============================================================
        print("\n" + "-" * 55)
        print("🩺 [ขั้นตอนที่ 2] ซักถามอาการและคัดกรองความเร่งด่วน (Triage)")
        print("-" * 55)

        symptoms = input("กรุณาระบุอาการเบื้องต้น: ").strip()
        while not symptoms:
            symptoms = input("กรุณาระบุอาการเบื้องต้น (ห้ามเว้นว่าง): ").strip()

        print("\nระดับความเร่งด่วน:")
        print("  [Red]    = ฉุกเฉินวิกฤต (รอ 0 นาที)")
        print("  [Yellow] = เร่งด่วน (รอ 15 นาที)")
        print("  [Green]  = ไม่เร่งด่วน (รอ 45 นาที)")
        print("  [White]  = ตรวจทั่วไป/นัดหมาย (รอ 60 นาที)")
        urgency_input = input("เลือกระดับความเร่งด่วน (Red/Yellow/Green/White) [ค่าเริ่มต้น Green]: ").strip().capitalize()
        urgency = urgency_input if urgency_input in ["Red", "Yellow", "Green", "White"] else "Green"

        queue = clinic.create_queue(patient.p_id, symptoms, urgency)
        print(f"\n🎟️ ออกบัตรคิวสำเร็จ! หมายเลขคิว: {queue.queue_number} (เวลารอโดยประมาณ {queue.waiting_time} นาที)")

        # ============================================================
        # 3. แพทย์ตรวจรักษาและบันทึกเวชระเบียน (Doctor Exam & Medical Record)
        # ============================================================
        print("\n" + "-" * 55)
        print("👨‍⚕️ [ขั้นตอนที่ 3] แพทย์ตรวจรักษาและคีย์ข้อมูลเวชระเบียน")
        print("-" * 55)

        print("รายชื่อแพทย์ผู้ตรวจรักษา:")
        for doc_id, doc_info in MedicalRecord.DOCTOR.items():
            print(f"  [{doc_id}] {doc_info['doctor_name']} ({doc_info['specialization']})")

        selected_doc = input("เลือกแพทย์ผู้ตรวจ (DOC001/DOC002/DOC003) [ค่าเริ่มต้น DOC001]: ").strip().upper()
        if selected_doc not in MedicalRecord.DOCTOR:
            selected_doc = "DOC001"

        doctor_info = MedicalRecord.DOCTOR[selected_doc]
        print(f"-> แพทย์ผู้รับผิดชอบ: {doctor_info['doctor_name']} ({doctor_info['specialization']})")

        diagnosis = input("\nกรุณากรอกผลการวินิจฉัยโรค (Diagnosis): ").strip()
        while not diagnosis:
            diagnosis = input("กรุณากรอกผลการวินิจฉัย (ห้ามเว้นว่าง): ").strip()

        status_input = input("สถานะการตรวจ (Status) [ค่าเริ่มต้น: เสร็จสิ้นการตรวจ]: ").strip()
        record_status = status_input if status_input else "เสร็จสิ้นการตรวจ"

        meds = input("กรุณากรอกรายการยาและคำแนะนำ (Prescribed Meds): ").strip()
        if not meds:
            meds = "ไม่มีการสั่งยาเพิ่มเติม (ดูแลสุขภาพตามคำแนะนำแพทย์)"

        record = clinic.create_medical_record(
            p_id=patient.p_id,
            doctor_id=selected_doc,
            diagnosis=diagnosis,
            prescribed_meds=meds,
            status=record_status
        )
        print(f"\n📋 บันทึกเวชระเบียนสำเร็จ! รหัสเอกสาร: [{record.record_id}]")

        # ============================================================
        # 4. ออกใบนัดหมายแพทย์ (Appointment Slip)
        # ============================================================
        print("\n" + "-" * 55)
        print("📅 [ขั้นตอนที่ 4] ออกใบนัดหมายแพทย์ (Appointment Slip)")
        print("-" * 55)

        want_appointment = input("ต้องการออกใบนัดติดตามอาการหรือไม่? (Y/N) [ค่าเริ่มต้น: Y]: ").strip().upper()
        if want_appointment != "N":
            default_next_week = (datetime.today().date() + timedelta(days=7)).strftime("%Y-%m-%d")
            app_date_input = input(f"กรุณากรอกวันที่นัดหมาย (YYYY-MM-DD) [กด Enter เพื่อนัด 7 วันข้างหน้า: {default_next_week}]: ").strip()
            appointment_date = app_date_input if app_date_input else default_next_week
            app_reason = input("ระบุวัตถุประสงค์การนัด (เช่น ติดตามผลเลือด, ดูอาการต่อเนื่อง) [ค่าเริ่มต้น: ติดตามผลการรักษา]: ").strip()
            if not app_reason:
                app_reason = "ติดตามผลการรักษา"

            # พิมพ์ใบนัดหมายแพทย์
            print("\n" + "=" * 60)
            print("                📅 ใบนัดหมายแพทย์ (APPOINTMENT SLIP)")
            print("                 คลินิกเวชกรรมสุขภาพดี (HealthCare)")
            print("=" * 60)
            print(f" รหัสประจำตัวคนไข้ (Patient_id) : {patient.p_id}")
            print(f" ชื่อ-นามสกุล (fullname)         : {patient.fullname}")
            print(f" เบอร์โทรศัพท์ (phone_num)       : {patient.phone_number}")
            print(f" แพทย์ผู้นัด (doctor_name)       : {record.doctor_name} ({record.doctor_specialization})")
            print(f" วันที่นัดหมาย (Date)            : {appointment_date}")
            print(f" วัตถุประสงค์การนัดหมาย           : {app_reason}")
            print(f" รายการยาที่ได้รับ              : {record.prescribed_meds}")
            print("=" * 60)
        else:
            print("-> ไม่มีการออกใบนัดหมายเพิ่มเติม")

        # ============================================================
        # 5. คิดเงิน ออกบิล และบันทึกการชำระเงิน (Billing & Payment)
        # ============================================================
        print("\n" + "-" * 55)
        print("💳 [ขั้นตอนที่ 5] คิดค่ารักษาและออกบิล (Billing & Payment)")
        print("-" * 55)

        # รับค่าธรรมเนียมการตรวจ
        while True:
            try:
                tf_input = input("กรุณากรอกค่าตรวจรักษา/หัตถการ (บาท) [ค่าเริ่มต้น 300]: ").strip()
                treatment_fee = float(tf_input) if tf_input else 300.0
                break
            except ValueError:
                print("❌ กรุณากรอกเป็นตัวเลขเท่านั้น")

        # รับค่ายา
        while True:
            try:
                mf_input = input("กรุณากรอกค่ายาและเวชภัณฑ์ (บาท) [ค่าเริ่มต้น 0]: ").strip()
                medication_fee = float(mf_input) if mf_input else 0.0
                break
            except ValueError:
                print("❌ กรุณากรอกเป็นตัวเลขเท่านั้น")

        # บันทึกบิล
        pay_confirm = input("\nต้องการบันทึกการชำระเงินทันทีหรือไม่? (Y/N) [ค่าเริ่มต้น: Y]: ").strip().upper()
        bill_status = "ชำระเงินเรียบร้อยแล้ว" if pay_confirm != "N" else "ยังไม่ชำระ"

        bill = clinic.create_bill(
            record_id=record.record_id,
            treatment_fee=treatment_fee,
            medication_fee=medication_fee,
            status=bill_status
        )

        # พิมพ์ใบแจ้งหนี้ / ใบเสร็จรับเงิน
        print("\n" + "=" * 60)
        print("           💳 ใบแจ้งหนี้ / ใบเสร็จรับเงิน (INVOICE / RECEIPT)")
        print("=" * 60)
        print(f" เลขที่ใบเสร็จ (Bill_id)          : {bill.bill_id}")
        print(f" รหัสเวชระเบียน (record_id)      : {record.record_id}")
        print(f" รหัสคนไข้ (Patient_id)          : {patient.p_id} ({patient.fullname})")
        print(f" เบอร์โทรศัพท์                   : {patient.phone_number}")
        print("-" * 60)
        print(f" ค่าตรวจรักษา/หัตถการ (Treatment) : {bill.treatment_fee:>12,.2f} บาท")
        print(f" ค่ายาและเวชภัณฑ์ (Medication)   : {bill.medication_fee:>12,.2f} บาท")
        print("-" * 60)
        print(f" ยอดรวมทั้งสิ้น (total_payment)    : {bill.total_payment:>12,.2f} บาท")
        print(f" สถานะการชำระเงิน                : {bill.status}")
        print("=" * 60)

        # ============================================================
        # 6. ยืนยันการบันทึกข้อมูลทุกอย่างเข้าระบบ
        # ============================================================
        print("\n🎉 บันทึกข้อมูลคนไข้, คิวตรวจ, เวชระเบียน, ใบนัด และบิลชำระเงิน เข้าระบบครบถ้วนสมบูรณ์!")
        print("=" * 65 + "\n")

        return clinic, patient, queue, record, bill

    except ValueError as e:
        print(f"\n❌ เกิดข้อผิดพลาดในข้อมูล: {e}")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดไม่คาดคิด: {e}")


# ---------------------------------------------------------
# Main Execution Entry Point
# ---------------------------------------------------------

    # 1. รันการจำลองระบบทั้งหมดตาม Crow's Foot Diagram และ Flowchart
#clinic_instance = run_demo_simulation()

clinic_test = ClinicSystem()

patient_df = pd.read_csv("https://raw.githubusercontent.com/Nxpze/git-try-101/refs/heads/main/patient.csv")
clinic_test.load_patients_from_dataframe(patient_df)
interactive_patient_entry(clinic_test)
    # 2. ปลดล็อกบรรทัดด้านล่างเมื่อต้องการทดสอบโหมด Interactive รับคนไข้จริง
    # print("\n>>> เริ่มต้นทดสอบโหมด Interactive รับคนไข้ ตรวจรักษา ใบนัด และคิดเงิน <<<")
    # interactive_patient_entry(clinic_instance)