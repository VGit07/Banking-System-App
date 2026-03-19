import customtkinter as ctk
import sqlite3 as sq


# Database Paths
BANK_DB = "Data/bank.db"
USER_DB = "User/user.db"


# Main Window 

app = ctk.CTk()
app.geometry("400x600")
app.title("Banking App")
app.iconbitmap("Icon/bank.ico")
app.resizable(False, False)

# For changing screens

main_frame = ctk.CTkFrame(app)
main_frame.pack(expand=True, fill="both")


# Utiligthy
def clear():
    """Remove all widgets from main_frame"""
    for widget in main_frame.winfo_children():
        widget.destroy()


# Login Screen

def sign_in():

    clear()

    def login():
        acc_no = account_entry.get()
        pwd = password_entry.get()

        with sq.connect(BANK_DB) as conn:
            cursor = conn.cursor()
            verify = """SELECT Customer_Name,Account_No,Password,Pin,Balance 
                        FROM customer WHERE Account_No=? AND Password=?"""
            cursor.execute(verify, (acc_no, pwd))
            row = cursor.fetchone()

        if row:
            # Save session in user.db
            with sq.connect(USER_DB) as user_conn:
                user_cursor = user_conn.cursor()

                user_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user(
                        Customer_Name TEXT,
                        Account_No INT,
                        Password TEXT,
                        Pin TEXT,
                        Balance REAL
                    )
                """)

                user_cursor.execute("DELETE FROM user")
                user_cursor.execute(
                    "INSERT INTO user VALUES (?, ?, ?, ?, ?)", row
                )
                user_conn.commit()

            dash()  # switch to dashboard
        else:
            error_label.configure(text="Invalid Account or Password")

    # UI
    ctk.CTkLabel(main_frame, text="Bank Login",
                 font=("Arial", 22, "bold")).pack(pady=40)

    account_entry = ctk.CTkEntry(main_frame,placeholder_text="Account Number",width=250,height=35,font=("Consolas", 15, "bold"))
    account_entry.pack(pady=10)

    password_entry = ctk.CTkEntry(main_frame,placeholder_text="Password",show="*",width=250,height=35,font=("Consolas", 15, "bold"))
    password_entry.pack(pady=10)

    ctk.CTkButton(main_frame,text="Login",command=login,fg_color="green",width=200,height=40,font=("Consolas", 25, "bold")).pack(pady=20)

    error_label = ctk.CTkLabel(main_frame, text="", text_color="red")
    error_label.pack()





# Dashboard
def dash():

    clear()

    # Get active user
    with sq.connect(USER_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        data = cursor.fetchone()

    if not data:
        sign_in()
        return
    
    name, acc_no, pwd, pin, balance = data

# --------------------------------------------------------------------------------------------------
# Deposit Logic 
# --------------------------------------------------------------------------------------------------
    def deposit():
        clear()
        # Deposit logic button function & logic
        def confirm_deposit():
            entered_pin = pin_entry.get()
            
            if entered_pin != pin:
                ctk.CTkLabel(main_frame,text="Wrong PIN",text_color="red").pack()
                return
            
            try:
                amt = float(amt_entry.get())
            
            except:
                ctk.CTkLabel(main_frame,text="Invalid amount",text_color="red").pack()
                return
            

            new_balance = balance + amt

            # Update session DB
            with sq.connect(USER_DB) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE user SET Balance=? WHERE Account_No=?",(new_balance, acc_no))
                conn.commit()

            # Update main bank DB
            with sq.connect(BANK_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE customer SET Balance=? WHERE Account_No=?",(new_balance, acc_no))
                conn.commit()
            clear()
            ctk.CTkLabel(main_frame,text=f"$ {amt} deposited successfully!",font=("Consolas", 20,"bold"),text_color="green").pack(pady=20,expand=True)
            ctk.CTkButton(main_frame,text="Back",font=("Consolas", 20,"bold"),fg_color="green",width=250,height=50,command=dash).pack(pady=20,expand=True)
        
        # Deposit Window 
        ctk.CTkLabel(main_frame,text="Deposit Money",font=("Consolas", 26, "bold")).pack(pady=20)
        amt_entry = ctk.CTkEntry(main_frame,placeholder_text="Enter the Amount",font=("Consolas", 20, "bold"),width=300,height=50)
        amt_entry.pack(pady=20)
        pin_entry = ctk.CTkEntry(main_frame,placeholder_text="4-Digit PIN",show="*",font=("Consolas", 20, "bold"),width=300,height=50)
        pin_entry.pack(pady=20)
            
        # Deposit button
        ctk.CTkButton(main_frame,text="Deposit",fg_color="green",width=250,height=50,font=("Consolas", 22, "bold"),command=confirm_deposit).pack(pady=10)
        
        # Back Button
        ctk.CTkButton(main_frame,text="Back",font=("Consolas", 20,"bold"),fg_color="green",width=250,height=50,command=dash).pack(pady=20)

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Payment Logic
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def payment():
        clear()
        
        # Create a persistent error label for feedback
        error_label = ctk.CTkLabel(main_frame, text="", text_color="red", font=("Consolas", 12))

        def confirm_pay():
            error_label.configure(text="") # Reset error message
            try:
                amt = float(amt_entry.get())
                pin_temp = pin_entry.get()
                acc_to = acc_entry.get()
                
                if amt <= 0:
                    error_label.configure(text="Amount must be greater than 0")
                    return
            except ValueError:
                error_label.configure(text="Please enter a valid numeric amount")
                return

            # 1. Security & Logic Checks
            if pin_temp != pin:
                error_label.configure(text="Incorrect PIN")
                return
            if amt > balance:
                error_label.configure(text="Insufficient funds")
                return
            if acc_to == str(acc_no):
                error_label.configure(text="Cannot pay yourself!")
                return

            # 2. Database Transaction
            try:
                with sq.connect(BANK_DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT Balance FROM customer WHERE Account_No = ?", (acc_to,))
                    receiver = cursor.fetchone()
                    
                    if not receiver:
                        error_label.configure(text="Receiver account not found")
                        return

                    # Perform the transfer
                    # Deduct from Sender
                    cursor.execute("UPDATE customer SET Balance = Balance - ? WHERE Account_No = ?", (amt, acc_no))
                    # Add to Receiver
                    cursor.execute("UPDATE customer SET Balance = Balance + ? WHERE Account_No = ?", (amt, acc_to))
                    
                    conn.commit()

                # 3. Update Local Session (USER_DB)
                new_bal = balance - amt
                with sq.connect(USER_DB) as u_conn:
                    u_conn.execute("UPDATE user SET Balance = ?", (new_bal,))
                    u_conn.commit()

                # 4. Success UI
                clear()
                ctk.CTkLabel(main_frame, text="Transfer Successful!", font=("Consolas", 24, "bold"), text_color="green").pack(pady=40)
                ctk.CTkLabel(main_frame, text=f"Sent $ {amt} to {acc_to}", font=("Consolas", 20)).pack(pady=10)
                ctk.CTkButton(main_frame,text="Back",font=("Consolas", 20,"bold"),fg_color="green",width=250,height=50,command=dash).pack(pady=20)

                
            except Exception as e:
                error_label.configure(text="Transaction failed. Try again.")

        # --- UI ---
        ctk.CTkLabel(main_frame, text="Pay Money", font=("Consolas", 26, "bold")).pack(pady=20)
        
        acc_entry = ctk.CTkEntry(main_frame, placeholder_text="Receiver Account No.", width=300, height=45, font=("Consolas", 20, "bold"))
        acc_entry.pack(pady=10)
        
        amt_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter the Amount", width=300, height=45, font=("Consolas", 20, "bold"))
        amt_entry.pack(pady=10)
        
        pin_entry = ctk.CTkEntry(main_frame, placeholder_text="4-Digit PIN", show="*", width=300, height=45, font=("Consolas", 20, "bold"))
        pin_entry.pack(pady=10)
        
        error_label.pack(pady=5)

        ctk.CTkButton(main_frame, text="Pay", fg_color="green", width=250, height=50, 
                      font=("Consolas", 20, "bold"), command=confirm_pay).pack(pady=10)
        
        ctk.CTkButton(main_frame, text="Back", fg_color="green", 
                      width=250, height=50,  font=("Consolas", 20, "bold"),command=dash).pack(pady=10)

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Balance Logic
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def bal():
        clear()
        ctk.CTkLabel(main_frame,text=f"Account no. : {acc_no}",font=("Consolas", 26, "bold")).pack(pady=20)
        ctk.CTkLabel(main_frame,text=f"Balance : $ {balance}",font=("Consolas", 26, "bold")).pack(pady=20)
        ctk.CTkButton(main_frame,text="Back",font=("Consolas", 20,"bold"),fg_color="green",width=250,height=50,command=dash).pack(pady=20)

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    

    def logout():
        # Clear session
        with sq.connect(USER_DB) as conn:
            conn.execute("DROP TABLE IF EXISTS user")
        sign_in()
    
    
    # UI
    ctk.CTkLabel(main_frame, text=f"Welcome, {name}", font=("Consolas", 22, "bold")).pack(pady=20)

    ctk.CTkLabel(main_frame, text=f"Account No: {acc_no}", font=("Consolas", 18)).pack(pady=10)

    ctk.CTkButton(main_frame, text="Deposit", fg_color="green", width=250, height=50, font=("Consolas", 22, "bold"),command=deposit).pack(pady=20)

    ctk.CTkButton(main_frame, text="Pay", fg_color="green", width=250, height=50, font=("Consolas", 22, "bold"),command=payment).pack(pady=20)

    ctk.CTkButton(main_frame, text="Balance",fg_color="green", width=250, height=50, font=("Consolas", 22, "bold"),command=bal).pack(pady=20)

    ctk.CTkButton(main_frame, text="Log Out", fg_color="red", width=250, height=50, font=("Consolas", 22, "bold"),command=logout).pack(pady=40)


# APP Starts

if __name__ == "__main__":
    with sq.connect(USER_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='user'
    """)
        session_exists = cursor.fetchone()
        if session_exists:
            dash()
        else:
            sign_in()
    app.mainloop()