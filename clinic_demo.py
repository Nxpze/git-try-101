from datetime import datetime, timedelta, date
import os
import re
import random
import pandas as pd


# ---------------------------------------------------------
# Database Path Configuration
# ---------------------------------------------------------
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
PATIENTS_FILE = os.path.join(DB_DIR, "patients_model.csv")
RECORDS_FILE = os.path.join(DB_DIR, "medical_records.csv")
BILLS_FILE = os.path.join(DB_DIR, "patients_bills.csv")
QUEUES_FILE = os.path.join(DB_DIR, "queues.csv")


# ---------------------------------------------------------
# Emergency Exit Exception & Safe Input Helper
# ---------------------------------------------------------
class EmergencyExit(Exception):
    """ข้อยกเว้นเมื่อผู้ใช้กด 'Q' เพื่อออกจากระบบฉุกเฉิน"""
    pass


def prompt_input(prompt_text, default=None, allow_empty=True):
    """
    รับ input จากผู้ใช้ โดยตรวจจับ 'Q' หรือ 'q' เพื่อออกจากระบบทันที
    """
    val = input(prompt_text).strip()
    if val.upper() == "Q":
        raise EmergencyExit("ผู้ใช้กด 'Q' เพื่อออกจากระบบทันที (Emergency Exit)")
    
    if not val and default is not None:
        return default
    
    if not val and not allow_empty:
        while not val:
            val = input(prompt_text).strip()
            if val.upper() == "Q":
                raise EmergencyExit("ผู้ใช้กด 'Q' เพื่อออกจากระบบทันที (Emergency Exit)")
    return val


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def parse_date(date_str):
    """แปลงข้อความวันที่ (YYYY-MM-DD หรือ YYYY/MM/DD หรือ DD/MM/YYYY) เป็น date object"""
    if isinstance(date_str, (datetime, date)):
        return date_str if isinstance(date_str, date) else date_str.date()

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: '{date_str}' (กรุณาใช้ YYYY-MM-DD หรือ YYYY/MM/DD)")


def age_calculator(dob):
    """คำนวณอายุจากวันเกิด"""
    try:
        birthdate = parse_date(dob)
        today = datetime.today().date()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age
    except Exception:
        return None


# ---------------------------------------------------------
# Entity Classes (Crow's Foot Diagram)
# ---------------------------------------------------------
class Patient:
    """
    PATIENT Entity (ตรงกับ patients_model.csv)
    - p_id (PK): string
    - fullname: string
    - dob: date string (YYYY-MM-DD)
    - age: int
    - phone_number: string
    - allergies: string
    - underlying_disease: string
    """
    def __init__(self, patient_id, fullname, dob, phone_number, allergies="ไม่มี", underlying_disease="ไม่มี", age=None):
        self.p_id = str(patient_id) if pd.notna(patient_id) else ""
        self.Patient_id = self.p_id
        self.fullname = str(fullname) if pd.notna(fullname) else ""
        self.dob = str(dob) if pd.notna(dob) else ""
        self.phone_number = str(phone_number) if pd.notna(phone_number) else ""
        self.allergies = str(allergies) if pd.notna(allergies) else "ไม่มี"
        self.underlying_disease = str(underlying_disease) if pd.notna(underlying_disease) else "ไม่มี"
        
        calculated_age = age_calculator(self.dob)
        if age is not None and pd.notna(age):
            try:
                self.age = int(float(age))
            except (ValueError, TypeError):
                self.age = calculated_age
        else:
            self.age = calculated_age

    def age_cal(self):
        return age_calculator(self.dob)

    def is_adult(self):
        return self.age is not None and self.age >= 20

    def to_dict(self):
        return {
            "p_id": self.p_id,
            "fullname": self.fullname,
            "dob": self.dob,
            "age": self.age,
            "phone_number": self.phone_number,
            "allergies": self.allergies,
            "underlying_disease": self.underlying_disease,
        }

    def __repr__(self):
        age_str = f"{self.age} ปี" if self.age is not None else "ไม่ระบุอายุ"
        return f"<Patient {self.p_id}: {self.fullname}, อายุ {age_str}, แพ้ยา: {self.allergies}>"


class Queue:
    """
    QUEUE Entity (ตรงกับ queues.csv)
    - queue_id (PK): string
    - p_id (FK): string
    - queue_number: string
    - symptoms: string
    - urgency_level: string (Red, Yellow, Green, White)
    - arrival_time: datetime string
    - waiting_time: int
    """
    def __init__(self, queue_id, patient_id, queue_number, symptoms, urgency_level, arrival_time=None, waiting_time=None, alert_status=None, recheck_count=0):
        self.queue_id = str(queue_id) if pd.notna(queue_id) else ""
        self.p_id = str(patient_id) if pd.notna(patient_id) else ""
        self.Patient_id = self.p_id
        self.Paient_id = self.p_id
        self.queue_number = str(queue_number) if pd.notna(queue_number) else ""
        self.symptoms = str(symptoms) if pd.notna(symptoms) else ""
        self.urgency_level = str(urgency_level) if pd.notna(urgency_level) else "Green"
        
        if arrival_time:
            self.arrival_time = arrival_time if isinstance(arrival_time, (datetime, str)) else str(arrival_time)
        else:
            self.arrival_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if waiting_time is not None and pd.notna(waiting_time):
            try:
                self.waiting_time = int(float(waiting_time))
            except (ValueError, TypeError):
                self.waiting_time = self.calculate_initial_waiting_time()
        else:
            self.waiting_time = self.calculate_initial_waiting_time()

        self.alert_status = alert_status if alert_status and pd.notna(alert_status) else "รอตามปกติ"
        try:
            self.recheck_count = int(float(recheck_count)) if pd.notna(recheck_count) else 0
        except (ValueError, TypeError):
            self.recheck_count = 0
            
        self.next_check_time = 30
        self.evaluate_alert_status()

    def calculate_initial_waiting_time(self):
        wait_matrix = {"Red": 0, "Yellow": 15, "Green": 45, "White": 60}
        return wait_matrix.get(self.urgency_level, 30)

    def evaluate_alert_status(self):
        if self.waiting_time >= 30 and self.alert_status != "ดันคิวทันที":
            self.alert_status = "ต้องรีเช็ค"

    def nurse_recheck(self, patient_condition, extension_minutes=30):
        self.recheck_count += 1
        if patient_condition == "อาการแย่ลง":
            self.fast_track_trigger()
        else:
            self.alert_status = "รอตามปกติ (รีเช็คแล้ว)"
            self.next_check_time += extension_minutes

    def fast_track_trigger(self):
        self.urgency_level = "Red"
        self.alert_status = "ดันคิวทันที"
        self.waiting_time = 0

    def to_dict(self):
        arr_str = self.arrival_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(self.arrival_time, datetime) else str(self.arrival_time)
        return {
            "queue_id": self.queue_id,
            "p_id": self.p_id,
            "queue_number": self.queue_number,
            "symptoms": self.symptoms,
            "urgency_level": self.urgency_level,
            "arrival_time": arr_str,
            "waiting_time": self.waiting_time,
            "alert_status": self.alert_status,
            "recheck_count": self.recheck_count,
        }

    def __repr__(self):
        return f"<Queue {self.queue_number} (ID: {self.queue_id}) | ผู้ป่วย: {self.p_id} | ระดับ: {self.urgency_level} | สถานะ: {self.alert_status}>"


class MedicalRecord:
    """
    MEDICAL_RECORD Entity (ตรงกับ medical_records.csv)
    - record_id (PK): string (e.g. TR001, REC001)
    - treatment_time: string / datetime
    - p_id (FK): string
    - doctor_id (FK): string (DOC001, DOC002, DOC003)
    - doctor_name: string
    - diagnosis: string
    - prescribed_meds: string
    - status: string
    """
    DOCTOR = {
        "DOC001": {
            "doctor_name": "นพ. สมชาย ใจดี",
            "specialization": "อายุรกรรม",
            "phone_number": "081-111-2233"
        },
        "DOC002": {
            "doctor_name": "พญ. วิภาดา รักษาดี",
            "specialization": "กุมารเวชศาสตร์ (หมอเด็ก)",
            "phone_number": "082-222-3344"
        },
        "DOC003": {
            "doctor_name": "นพ. ธนกฤต เก่งกาจ",
            "specialization": "ศัลยกรรมกระดูกและข้อ",
            "phone_number": "083-333-4455"
        }
    }

    def __init__(self, record_id, p_id, doctor_id="DOC001", diagnosis="", prescribed_meds="", status="เสร็จสิ้นการตรวจ", treatment_time=None, doctor_name=None):
        self.record_id = str(record_id) if pd.notna(record_id) else ""
        self.p_id = str(p_id) if pd.notna(p_id) else ""
        self.Patient_id = self.p_id
        
        # Ensure doctor_id always uses DOC format
        raw_doc_id = str(doctor_id) if pd.notna(doctor_id) else "DOC001"
        if raw_doc_id.startswith("D") and not raw_doc_id.startswith("DOC"):
            raw_doc_id = re.sub(r"^D(?=\d)", "DOC", raw_doc_id)
        self.doctor_id = raw_doc_id
        self.d_id = self.doctor_id

        doctor_info = self.DOCTOR.get(self.doctor_id, {
            "doctor_name": doctor_name if doctor_name and pd.notna(doctor_name) else "ไม่พบข้อมูลแพทย์",
            "specialization": "ไม่ระบุ",
            "phone_number": "ไม่ระบุ"
        })

        self.doctor_name = doctor_name if doctor_name and pd.notna(doctor_name) else doctor_info.get("doctor_name")
        self.doctor_specialization = doctor_info.get("specialization", "ไม่ระบุ")
        self.doctor_phone = doctor_info.get("phone_number", "ไม่ระบุ")
        
        if treatment_time:
            self.treatment_time = treatment_time if isinstance(treatment_time, str) else str(treatment_time)
        else:
            self.treatment_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.record_date = self.treatment_time

        self.diagnosis = str(diagnosis) if pd.notna(diagnosis) else ""
        self.status = str(status) if pd.notna(status) else "เสร็จสิ้นการตรวจ"
        self.prescribed_meds = str(prescribed_meds) if pd.notna(prescribed_meds) else ""

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "treatment_time": self.treatment_time,
            "p_id": self.p_id,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "diagnosis": self.diagnosis,
            "prescribed_meds": self.prescribed_meds,
            "status": self.status,
        }

    def __repr__(self):
        return f"<MedicalRecord {self.record_id} | ผู้ป่วย: {self.p_id} | แพทย์: {self.doctor_name} ({self.doctor_id}) โทร: {self.doctor_phone} | วินิจฉัย: {self.diagnosis}>"


class Bill:
    """
    BILL Entity (ตรงกับ patients_bills.csv)
    - bill_id (PK): string (e.g. B0001, B001)
    - record_id (FK): string (e.g. TR001)
    - patient_id (FK): string (e.g. P107)
    - treatment_fee: decimal/float
    - medication_fee: decimal/float
    - total_payment: decimal/float
    - status: string
    """
    def __init__(self, bill_id, record_id, patient_id, treatment_fee=0.0, medication_fee=0.0, total_payment=None, status="ยังไม่ชำระ"):
        self.bill_id = str(bill_id) if pd.notna(bill_id) else ""
        self.record_id = str(record_id) if pd.notna(record_id) else ""
        self.patient_id = str(patient_id) if pd.notna(patient_id) else ""
        self.p_id = self.patient_id
        self.Patient_id = self.patient_id

        try:
            self.treatment_fee = float(treatment_fee) if pd.notna(treatment_fee) else 0.0
        except (ValueError, TypeError):
            self.treatment_fee = 0.0

        try:
            self.medication_fee = float(medication_fee) if pd.notna(medication_fee) else 0.0
        except (ValueError, TypeError):
            self.medication_fee = 0.0

        if total_payment is not None and pd.notna(total_payment):
            try:
                self.total_payment = float(total_payment)
            except (ValueError, TypeError):
                self.total_payment = self.calculate_total_payment()
        else:
            self.total_payment = self.calculate_total_payment()

        self.status = str(status) if pd.notna(status) else "ยังไม่ชำระ"

    def calculate_total_payment(self):
        return round(self.treatment_fee + self.medication_fee, 2)

    def pay(self):
        """บันทึกการชำระเงิน"""
        self.status = "ชำระแล้ว"
        return self.total_payment

    def to_dict(self):
        return {
            "bill_id": self.bill_id,
            "record_id": self.record_id,
            "patient_id": self.patient_id,
            "treatment_fee": self.treatment_fee,
            "medication_fee": self.medication_fee,
            "total_payment": self.total_payment,
            "status": self.status,
        }

    def __repr__(self):
        return f"<Bill {self.bill_id} | ผู้ป่วย: {self.patient_id} | ยอดรวม: {self.total_payment:,.2f} บาท | สถานะ: {self.status}>"


# ---------------------------------------------------------
# ---------------------------------------------------------
# Clinic Management System Controller
# ---------------------------------------------------------
class ClinicSystem:
    """ระบบบริหารจัดการคลินิก เชื่อมโยง Patient, Queue, MedicalRecord, Bill และ CSV Database"""

    def __init__(self, auto_load=True):
        self.patients = {}        # p_id -> Patient
        self.queues = {}          # queue_id -> Queue
        self.medical_records = {} # record_id -> MedicalRecord
        self.bills = {}           # bill_id -> Bill

        # ตัวนับรหัสอัตโนมัติ
        self._patient_counter = 1
        self._queue_counter = 1
        self._record_counter = 1
        self._bill_counter = 1

        if auto_load:
            self.load_all_from_csv()

    def _init_counters(self):
        """คำนวณหมายเลขรหัสถัดไปจากข้อมูลที่มีอยู่ในฐานข้อมูล"""
        p_nums = [int(m.group()) for pid in self.patients for m in [re.search(r'\d+', str(pid))] if m]
        self._patient_counter = max(p_nums) + 1 if p_nums else 1

        q_nums = [int(m.group()) for qid in self.queues for m in [re.search(r'\d+', str(qid))] if m]
        self._queue_counter = max(q_nums) + 1 if q_nums else 1

        r_nums = [int(m.group()) for rid in self.medical_records for m in [re.search(r'\d+', str(rid))] if m]
        self._record_counter = max(r_nums) + 1 if r_nums else 1

        b_nums = [int(m.group()) for bid in self.bills for m in [re.search(r'\d+', str(bid))] if m]
        self._bill_counter = max(b_nums) + 1 if b_nums else 1

    # =========================================================
    # CSV Database Operations (Load & Save)
    # =========================================================
    def load_all_from_csv(self):
        """โหลดข้อมูลทั้งหมดจากไฟล์ CSV ในโฟลเดอร์ database/ เข้าระบบ"""
        # 1. โหลดข้อมูลคนไข้ (patients_model.csv)
        if os.path.exists(PATIENTS_FILE):
            try:
                df_p = pd.read_csv(PATIENTS_FILE, encoding="utf-8-sig")
                for _, row in df_p.iterrows():
                    p_id = str(row.get("p_id", "")).strip()
                    if not p_id or p_id == "nan":
                        continue
                    p = Patient(
                        patient_id=p_id,
                        fullname=row.get("fullname", ""),
                        dob=row.get("dob", ""),
                        phone_number=row.get("phone_number", ""),
                        allergies=row.get("allergies", "ไม่มี"),
                        underlying_disease=row.get("underlying_disease", "ไม่มี"),
                        age=row.get("age", None)
                    )
                    self.patients[p.p_id] = p
                print(f"📥 [Database] โหลดข้อมูลคนไข้สำเร็จ {len(self.patients)} รายการ")
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการโหลด {PATIENTS_FILE}: {e}")

        # 2. โหลดเวชระเบียน (medical_records.csv)
        if os.path.exists(RECORDS_FILE):
            try:
                df_r = pd.read_csv(RECORDS_FILE, encoding="utf-8-sig")
                for _, row in df_r.iterrows():
                    rec_id = str(row.get("record_id", "")).strip()
                    if not rec_id or rec_id == "nan":
                        continue
                    rec = MedicalRecord(
                        record_id=rec_id,
                        p_id=row.get("p_id", ""),
                        doctor_id=row.get("doctor_id", "DOC001"),
                        doctor_name=row.get("doctor_name", None),
                        diagnosis=row.get("diagnosis", ""),
                        prescribed_meds=row.get("prescribed_meds", ""),
                        status=row.get("status", "เสร็จสิ้นการตรวจ"),
                        treatment_time=row.get("treatment_time", None)
                    )
                    self.medical_records[rec.record_id] = rec
                print(f"📥 [Database] โหลดข้อมูลเวชระเบียนสำเร็จ {len(self.medical_records)} รายการ")
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการโหลด {RECORDS_FILE}: {e}")

        # 3. โหลดบิล/ใบเสร็จ (patients_bills.csv)
        if os.path.exists(BILLS_FILE):
            try:
                df_b = pd.read_csv(BILLS_FILE, encoding="utf-8-sig")
                for _, row in df_b.iterrows():
                    bill_id = str(row.get("bill_id", "")).strip()
                    if not bill_id or bill_id == "nan":
                        continue
                    patient_id = row.get("patient_id", row.get("p_id", ""))
                    bill = Bill(
                        bill_id=bill_id,
                        record_id=row.get("record_id", ""),
                        patient_id=patient_id,
                        treatment_fee=row.get("treatment_fee", 0.0),
                        medication_fee=row.get("medication_fee", 0.0),
                        total_payment=row.get("total_payment", None),
                        status=row.get("status", "รอชำระเงิน")
                    )
                    self.bills[bill.bill_id] = bill
                print(f"📥 [Database] โหลดข้อมูลใบแจ้งหนี้/บิลสำเร็จ {len(self.bills)} รายการ")
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการโหลด {BILLS_FILE}: {e}")

        # 4. โหลดคิว (queues.csv - ถ้ามี)
        if os.path.exists(QUEUES_FILE):
            try:
                df_q = pd.read_csv(QUEUES_FILE, encoding="utf-8-sig")
                for _, row in df_q.iterrows():
                    q_id = str(row.get("queue_id", "")).strip()
                    if not q_id or q_id == "nan":
                        continue
                    q = Queue(
                        queue_id=q_id,
                        patient_id=row.get("p_id", ""),
                        queue_number=row.get("queue_number", ""),
                        symptoms=row.get("symptoms", ""),
                        urgency_level=row.get("urgency_level", "Green"),
                        arrival_time=row.get("arrival_time", None),
                        waiting_time=row.get("waiting_time", None),
                        alert_status=row.get("alert_status", None),
                        recheck_count=row.get("recheck_count", 0)
                    )
                    self.queues[q.queue_id] = q
                print(f"📥 [Database] โหลดข้อมูลคิวสำเร็จ {len(self.queues)} รายการ")
            except Exception as e:
                print(f"⚠️ เกิดข้อผิดพลาดในการโหลด {QUEUES_FILE}: {e}")

        # อัปเดตตัวนับรหัสหลังจากโหลดเสร็จ
        self._init_counters()

    def save_all_to_csv(self):
        """บันทึกข้อมูลทั้งหมดลงไฟล์ CSV ในโฟลเดอร์ database/ ทันที"""
        os.makedirs(DB_DIR, exist_ok=True)
        try:
            if self.patients:
                df_p = pd.DataFrame([p.to_dict() for p in self.patients.values()])
                df_p.to_csv(PATIENTS_FILE, index=False, encoding="utf-8-sig")
            if self.medical_records:
                df_r = pd.DataFrame([r.to_dict() for r in self.medical_records.values()])
                df_r.to_csv(RECORDS_FILE, index=False, encoding="utf-8-sig")
            if self.bills:
                df_b = pd.DataFrame([b.to_dict() for b in self.bills.values()])
                df_b.to_csv(BILLS_FILE, index=False, encoding="utf-8-sig")
            if self.queues:
                df_q = pd.DataFrame([q.to_dict() for q in self.queues.values()])
                df_q.to_csv(QUEUES_FILE, index=False, encoding="utf-8-sig")
            print("💾 [Database] บันทึกข้อมูลทั้งหมดลงฐานข้อมูล CSV เรียบร้อยแล้ว")
        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในการบันทึกข้อมูลลง CSV: {e}")

    # =========================================================
    # Clinical Operations
    # =========================================================
    # 1. จัดการข้อมูลคนไข้ (PATIENT)
    def register_patient(self, fullname, dob, phone_number, allergies="ไม่มี", underlying_disease="ไม่มี", p_id=None, auto_save=True):
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
        if auto_save:
            self.save_all_to_csv()
        return patient

    # 2. ออกคิวและคัดกรองอาการ (QUEUE)
    def create_queue(self, p_id, symptoms, urgency_level="Green", arrival_time=None, auto_save=True):
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
        if auto_save:
            self.save_all_to_csv()
        return queue

    # 3. พยาบาลรีเช็คอาการ
    def nurse_recheck_queue(self, queue_id, patient_condition, extension_minutes=30, auto_save=True):
        if queue_id not in self.queues:
            raise ValueError(f"ไม่พบคิวรหัส: {queue_id}")

        queue = self.queues[queue_id]
        queue.nurse_recheck(patient_condition, extension_minutes)
        if auto_save:
            self.save_all_to_csv()
        return queue

    # 4. บันทึกผลการตรวจรักษา (MEDICAL_RECORD)
    def create_medical_record(self, p_id, doctor_id, diagnosis, prescribed_meds, status="เสร็จสิ้นการตรวจ", record_date=None, treatment_time=None, doctor_name=None, auto_save=True):
        record_id = f"TR{self._record_counter:03d}"
        self._record_counter += 1

        record = MedicalRecord(
            record_id=record_id,
            p_id=p_id,
            doctor_id=doctor_id,
            diagnosis=diagnosis,
            prescribed_meds=prescribed_meds,
            status=status,
            treatment_time=treatment_time,
            doctor_name=doctor_name
        )
        self.medical_records[record.record_id] = record
        if auto_save:
            self.save_all_to_csv()
        return record

    # 5. ออกใบเสร็จและการเงิน (BILL)
    def create_bill(self, record_id, treatment_fee=0.0, medication_fee=0.0, status="รอชำระเงิน", patient_id=None, auto_save=True):
        bill_id = f"B{self._bill_counter:04d}"
        self._bill_counter += 1

        if not patient_id:
            rec = self.medical_records.get(record_id)
            patient_id = rec.p_id if rec else ""

        bill = Bill(
            bill_id=bill_id,
            record_id=record_id,
            patient_id=patient_id,
            treatment_fee=treatment_fee,
            medication_fee=medication_fee,
            status=status
        )
        self.bills[bill.bill_id] = bill
        if auto_save:
            self.save_all_to_csv()
        return bill

    def pay_bill(self, bill_id, auto_save=True):
        if bill_id not in self.bills:
            raise ValueError(f"ไม่พบใบแจ้งหนี้รหัส: {bill_id}")
        bill = self.bills[bill_id]
        bill.pay()
        if auto_save:
            self.save_all_to_csv()
        return bill

    # 6. ค้นหาประวัติคนไข้แบบองค์รวม (Patient History View)
    def get_patient_summary(self, p_id):
        patient = self.patients.get(p_id)
        if not patient:
            return None

        p_queues = [q for q in self.queues.values() if q.p_id == p_id]
        p_records = [r for r in self.medical_records.values() if r.p_id == p_id]
        p_bills = [b for b in self.bills.values() if b.p_id == p_id or b.patient_id == p_id]

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
            p_id = str(row.get("p_id")) if pd.notna(row.get("p_id")) else None
            self.register_patient(
                fullname=row.get("fullname", ""),
                dob=str(row.get("dob", "")),
                phone_number=str(row.get("phone_number", "")),
                allergies=row.get("allergies", "ไม่มี"),
                underlying_disease=row.get("underlying_disease", "ไม่มี"),
                p_id=p_id,
                auto_save=False
            )
            count += 1
        self.save_all_to_csv()
        print(f"✅ โหลดข้อมูลคนไข้จาก DataFrame สำเร็จทั้งหมด {count} รายการ")

    def load_patients_from_csv(self, file_path):
        """อ่านไฟล์ CSV และโหลดข้อมูลคนไข้เข้าสู่ระบบอัตโนมัติ"""
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        self.load_patients_from_dataframe(df)


# ---------------------------------------------------------
# Interactive Patient Workflow
# ---------------------------------------------------------
def interactive_patient_entry(clinic=None):
    """
    โหมดบริการคนไข้แบบครบวงจร (Full Clinical Workflow):
    1. ตรวจสอบคนไข้เก่า/ลงทะเบียนคนไข้ใหม่ (รองรับการกด 'Q' เพื่อออกและบันทึกข้อมูลทันที)
    2. คัดกรองอาการและออกบัตรคิว (Triage & Queue)
    3. แพทย์ตรวจรักษา บันทึกการวินิจฉัย (Diagnosis), สถานะ (Status), รายการยา (Prescribed Meds)
    4. ออกใบนัดหมายแพทย์ (Appointment Slip) ที่มี Patient_id, fullname, doctor_name, phone_num, วันที่นัด
    5. คิดเงิน ออกบิลคำนวณ total_payment (ค่าตรวจ + ค่ายา) และบันทึกข้อมูลทุกอย่างลงฐานข้อมูล CSV
    """
    print("\n" + "=" * 65)
    print("🏥 ระบบงานบริการคนไข้ครบวงจร (Full Clinic Workflow System)")
    print("💡 ข้อแนะนำ: คุณสามารถพิมพ์ 'Q' หรือ 'q' ได้ตลอดเวลา เพื่อออกจากระบบและบันทึกข้อมูลทันที")
    print("=" * 65)

    if clinic is None:
        clinic = ClinicSystem(auto_load=True)

    patient = None
    queue = None
    record = None
    bill = None

    try:
        # ============================================================
        # 1. ตรวจสอบคนไข้เดิม หรือ ลงทะเบียนคนไข้ใหม่
        # ============================================================
        print("\n--- [ขั้นตอนที่ 1] ค้นหาประวัติ / ลงทะเบียนคนไข้ ---")
        patient_id = prompt_input("กรุณากรอกรหัสประจำตัวคนไข้ (P_id) [ถ้าคนไข้ใหม่กด Enter ข้าม]: ")

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

            fullname = ""
            dob = ""
            phone = ""
            allergies = "ไม่มี"
            disease = "ไม่มี"

            try:
                fullname = prompt_input("กรุณากรอกชื่อ-นามสกุลคนไข้: ", allow_empty=False)
                dob = prompt_input("กรุณากรอกวันเกิด (YYYY-MM-DD หรือ YYYY/MM/DD): ")
                phone = prompt_input("กรุณากรอกเบอร์โทรศัพท์: ")
                allergies = prompt_input("ประวัติการแพ้ยา (ถ้าไม่มีกด Enter): ", default="ไม่มี")
                disease = prompt_input("โรคประจำตัว (ถ้าไม่มีกด Enter): ", default="ไม่มี")
            except EmergencyExit:
                if fullname:
                    patient = clinic.register_patient(
                        fullname=fullname,
                        dob=dob if dob else "ไม่ระบุ",
                        phone_number=phone if phone else "ไม่ระบุ",
                        allergies=allergies,
                        underlying_disease=disease,
                        p_id=patient_id if patient_id else None
                    )
                    print(f"📌 [Partial Save] ลงทะเบียนข้อมูลคนไข้บางส่วน: [{patient.p_id}] {patient.fullname}")
                raise

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

        symptoms = ""
        urgency = "Green"
        try:
            symptoms = prompt_input("กรุณาระบุอาการเบื้องต้น: ", allow_empty=False)

            print("\nระดับความเร่งด่วน:")
            print("  [Red]    = ฉุกเฉินวิกฤต (รอ 0 นาที)")
            print("  [Yellow] = เร่งด่วน (รอ 15 นาที)")
            print("  [Green]  = ไม่เร่งด่วน (รอ 45 นาที)")
            print("  [White]  = ตรวจทั่วไป/นัดหมาย (รอ 60 นาที)")
            urgency_input = prompt_input("เลือกระดับความเร่งด่วน (Red/Yellow/Green/White) [ค่าเริ่มต้น Green]: ", default="Green").capitalize()
            urgency = urgency_input if urgency_input in ["Red", "Yellow", "Green", "White"] else "Green"
        except EmergencyExit:
            if symptoms and patient:
                queue = clinic.create_queue(patient.p_id, symptoms, urgency)
                print(f"📌 [Partial Save] บันทึกคิวตรวจบางส่วน: [{queue.queue_number}]")
            raise

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
            print(f"  [{doc_id}] {doc_info.get('doctor_name')} ({doc_info.get('specialization')}) - โทร: {doc_info.get('phone_number')}")

        selected_doc = "DOC001"
        diagnosis = ""
        record_status = "หายขาด"
        meds = "ไม่มีการสั่งยาเพิ่มเติม (ดูแลสุขภาพตามคำแนะนำแพทย์)"

        try:
            selected_doc_in = prompt_input("เลือกแพทย์ผู้ตรวจ (DOC001/DOC002/DOC003) [ค่าเริ่มต้น DOC001]: ", default="DOC001").upper()
            if selected_doc_in in MedicalRecord.DOCTOR:
                selected_doc = selected_doc_in
            elif selected_doc_in.replace("D", "DOC", 1) in MedicalRecord.DOCTOR:
                selected_doc = selected_doc_in.replace("D", "DOC", 1)
            elif f"DOC{selected_doc_in}" in MedicalRecord.DOCTOR:
                selected_doc = f"DOC{selected_doc_in}"
            else:
                selected_doc = "DOC001"

            doctor_info = MedicalRecord.DOCTOR[selected_doc]
            print(f"-> แพทย์ผู้รับผิดชอบ: {doctor_info['doctor_name']} ({doctor_info['specialization']}) - โทร: {doctor_info.get('phone_number')}")

            diagnosis = prompt_input("\nกรุณากรอกผลการวินิจฉัยโรค (Diagnosis): ", allow_empty=False)
            status_input = prompt_input("สถานะการตรวจ (Status) [ค่าเริ่มต้น: หายขาด]: ", default="หายขาด")
            record_status = status_input if status_input else "หายขาด"

            meds_input = prompt_input("กรุณากรอกรายการยาและคำแนะนำ (Prescribed Meds): ", default="ไม่มีการสั่งยาเพิ่มเติม (ดูแลสุขภาพตามคำแนะนำแพทย์)")
            meds = meds_input if meds_input else "ไม่มีการสั่งยาเพิ่มเติม (ดูแลสุขภาพตามคำแนะนำแพทย์)"
        except EmergencyExit:
            if diagnosis and patient:
                record = clinic.create_medical_record(
                    p_id=patient.p_id,
                    doctor_id=selected_doc,
                    diagnosis=diagnosis,
                    prescribed_meds=meds,
                    status=record_status
                )
                print(f"📌 [Partial Save] บันทึกเวชระเบียนบางส่วน: [{record.record_id}]")
            raise

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

        want_appointment = prompt_input("ต้องการออกใบนัดติดตามอาการหรือไม่? (Y/N) [ค่าเริ่มต้น: N]: ", default="N").upper()
        if want_appointment == "Y":
            default_next_week = (datetime.today().date() + timedelta(days=7)).strftime("%Y-%m-%d")
            app_date_input = prompt_input(f"กรุณากรอกวันที่นัดหมาย (YYYY-MM-DD) [กด Enter เพื่อนัด 7 วันข้างหน้า: {default_next_week}]: ", default=default_next_week)
            appointment_date = app_date_input if app_date_input else default_next_week
            app_reason = prompt_input("ระบุวัตถุประสงค์การนัด (เช่น ติดตามผลเลือด, ดูอาการต่อเนื่อง) [ค่าเริ่มต้น: ติดตามผลการรักษา]: ", default="ติดตามผลการรักษา")

            # พิมพ์ใบนัดหมายแพทย์
            print("\n" + "=" * 60)
            print("                📅 ใบนัดหมายแพทย์ (APPOINTMENT SLIP)")
            print("                 คลินิกเวชกรรมสุขภาพดี (HealthCare)")
            print("=" * 60)
            print(f" รหัสประจำตัวคนไข้ (Patient_id)   : {patient.p_id}")
            print(f" ชื่อ-นามสกุล (fullname)           : {patient.fullname}")
            print(f" เบอร์โทรศัพท์คนไข้ (phone_num)    : {patient.phone_number}")
            print(f" แพทย์ผู้นัด (doctor_name)         : {record.doctor_name} ({record.doctor_specialization})")
            print(f" เบอร์โทรศัพท์แพทย์ (doctor_phone) : {record.doctor_phone}")
            print(f" วันที่นัดหมาย (Date)              : {appointment_date}")
            print(f" วัตถุประสงค์การนัดหมาย             : {app_reason}")
            print(f" รายการยาที่ได้รับ                : {record.prescribed_meds}")
            print("=" * 60)
        else:
            print("-> ไม่มีการออกใบนัดหมายเพิ่มเติม")

        # ============================================================
        # 5. คิดเงิน ออกบิล และบันทึกการชำระเงิน (Billing & Payment)
        # ============================================================
        print("\n" + "-" * 55)
        print("💳 [ขั้นตอนที่ 5] คิดค่ารักษาและออกบิล (Billing & Payment)")
        print("-" * 55)

        treatment_fee = 300.0
        medication_fee = 0.0
        bill_status = "ชำระแล้ว"

        try:
            # รับค่าธรรมเนียมการตรวจ
            while True:
                try:
                    tf_input = prompt_input("กรุณากรอกค่าตรวจรักษา/หัตถการ (บาท) [ค่าเริ่มต้น 300]: ", default="300")
                    treatment_fee = float(tf_input)
                    break
                except ValueError:
                    print("❌ กรุณากรอกเป็นตัวเลขเท่านั้น")

            # รับค่ายา
            while True:
                try:
                    mf_input = prompt_input("กรุณากรอกค่ายาและเวชภัณฑ์ (บาท) [ค่าเริ่มต้น 0]: ", default="0")
                    medication_fee = float(mf_input)
                    break
                except ValueError:
                    print("❌ กรุณากรอกเป็นตัวเลขเท่านั้น")

            # บันทึกบิล
            pay_confirm = prompt_input("\nต้องการบันทึกการชำระเงินทันทีหรือไม่? (Y/N) [ค่าเริ่มต้น: Y]: ", default="Y").upper()
            bill_status = "ชำระแล้ว" if pay_confirm != "N" else "รอชำระเงิน"
        except EmergencyExit:
            if patient:
                bill = clinic.create_bill(
                    record_id=record.record_id if record else "",
                    patient_id=patient.p_id,
                    treatment_fee=treatment_fee,
                    medication_fee=medication_fee,
                    status="รอชำระเงิน"
                )
                print(f"📌 [Partial Save] บันทึกใบเสร็จเบื้องต้น: [{bill.bill_id}]")
            raise

        bill = clinic.create_bill(
            record_id=record.record_id if record else "",
            patient_id=patient.p_id if patient else "",
            treatment_fee=treatment_fee,
            medication_fee=medication_fee,
            status=bill_status
        )

        # พิมพ์ใบแจ้งหนี้ / ใบเสร็จรับเงิน
        print("\n" + "=" * 60)
        print("           💳 ใบแจ้งหนี้ / ใบเสร็จรับเงิน (INVOICE / RECEIPT)")
        print("=" * 60)
        print(f" เลขที่ใบเสร็จ (Bill_id)          : {bill.bill_id}")
        print(f" รหัสเวชระเบียน (record_id)      : {bill.record_id}")
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
        print("\n🎉 บันทึกข้อมูลคนไข้, คิวตรวจ, เวชระเบียน, ใบนัด และบิลชำระเงิน เข้าระบบและฐานข้อมูล CSV เรียบร้อยแล้ว!")
        print("=" * 65 + "\n")

        return clinic, patient, queue, record, bill

    except EmergencyExit as e:
        print(f"\n\n🛑 [Emergency Exit] {e}")
        print("💾 กำลังบันทึกข้อมูลที่มีอยู่ทั้งหมดเข้าสู่ฐานข้อมูล CSV...")
        clinic.save_all_to_csv()
        print("✅ บันทึกข้อมูลเข้าฐานข้อมูล CSV เรียบร้อยแล้ว ออกจากโปรแกรมอย่างปลอดภัย")
        return clinic, patient, queue, record, bill

    except ValueError as e:
        print(f"\n❌ เกิดข้อผิดพลาดในข้อมูล: {e}")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดไม่คาดคิด: {e}")


# ---------------------------------------------------------
# Main Execution Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    clinic = ClinicSystem(auto_load=True)
    interactive_patient_entry(clinic)