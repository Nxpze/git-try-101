from datetime import date
import random


def age_calculator(year, month, day, name):
    today = date.today()
    birthdate = date(year, month, day)
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

if __name__ == "__main__":
    try:
        name = input("กรุณากรอกชื่อของคุณ: ")
        year = int(input("กรุณากรอกปีเกิดของคุณ (คริสต์ศักราช) (YYYY): "))
        month = int(input("กรุณากรอกเดือนเกิดของคุณ (MM): "))
        day = int(input("กรุณากรอกวันเกิดของคุณ (DD): "))

        age = age_calculator(year, month, day, name)
        if age >= 20:
            print(f"คุณยังบรรลุนิติภาวะแล้ว {name} อายุ {age} ปี")
        else:
            print(f"คุณยังไม่บรรลุนิติภาวะ {name} อายุ {age} ปี")
    except ValueError:
        print("กรุณากรอกข้อมูลให้ถูกต้อง")
        exit()

#just a tester one don't mind it
sdhdnxkld = random.randint(1, 100)


