import csv
import qrcode
import os


def generate_qr_codes(csv_file):
    # Ensure the 'qr_codes' directory exists
    if not os.path.exists('qr_codes'):
        os.makedirs('qr_codes')

    try:
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
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
                except KeyError as e:
                    print(f"Missing expected column in CSV: {e}")
                except Exception as e:
                    print(f"An error occurred while generating QR code for {row['last_name']} {row['first_name']}: {e}")
    except FileNotFoundError:
        print(f"The file {csv_file} was not found.")
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")


generate_qr_codes('users.csv')
