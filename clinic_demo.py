from datetime import datetime, timedelta, date
import random
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd


class Patient:
  def __init__(self, patient_id, fullname, dob, phone_number, allergies="ไม่มี", underlying_disease="ไม่มี",):
    self.Patient_id = patient_id
    self.fullname = fullname
    self.dob = dob
    self.phone_number = phone_number
    self.allergies = allergies
    self.underlying_disease = underlying_disease
    self.age = self.age_cal()

  def age_cal(self):
    birthdate = datetime.strptime(self.dob, "%Y-%m-%d").date()
    today = datetime.today().date()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

class Queue:
  def __init__(self, queue_id, patient_id, queue_number, symptoms, urgency_level, arrival_time):
    self.queue_id = queue_id
    self.Paient_id = patient_id
    self.queue_number = queue_number
    self.symptoms = symptoms
    self.urgency_level = urgency_level  # Red, Yellow, Green, White
    self.arrival_time = arrival_time

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
    # เตือนครั้งแรกเมื่อรอครบ 30 นาที
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

class MedicalRecord:
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
    def __init__(self, record_id, patient_id, doctor_id, record_date, diagnosis, status, prescribed_meds, ):
      self.record_id = record_id
      self.Patient_id = patient_id

      doctor_info = self.DOCTOR.get(doctor_id, {
            "doctor_name": "ไม่พบข้อมูลแพทย์",
            "specialization": "ไม่ระบุ"
        })

      self.doctor_id = doctor_id
      self.doctor_name = doctor_info.get("doctor_name")
      self.doctor_specialization = doctor_info.get("specialization")

      self.record_date = record_date
      self.diagnosis = diagnosis
      self.status = status
      self.prescribed_meds = prescribed_meds



class Bill:
  def __init__(self, bill_id, record_id, patient_id, treatment_fee, medication_fee, status):
    self.bill_id = bill_id
    self.record_id = record_id
    self.Patient_id = patient_id
    self.treatment_fee = treatment_fee
    self.medication_fee = medication_fee
    self.total_payment = self.calculate_total_payment()
    self.status = status

  def calculate_total_payment(self):
    return round(self.treatment_fee + self.medication_fee, 2)