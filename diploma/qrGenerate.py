import csv
import qrcode


def generate_qr_codes(csv_file):
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            user_data = f"{row['last_name']},{row['first_name']},{row['middle_name']},{row['roles']},{row['group_id']},{row['department']},{row['start_date']},{row['end_date']}"
            qr.add_data(user_data)
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            img.save(f"qr_codes/{row['last_name']}_{row['first_name']}.png")


generate_qr_codes('users.csv')
