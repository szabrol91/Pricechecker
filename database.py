import sqlite3
from fileinput import filename
from tkinter import messagebox, filedialog
import csv
from datetime import datetime
import os


class Database:
    # EN: Simple SQLite data-access layer for the app.
    # HU: Egyszerű SQLite adat-hozzáférési réteg az alkalmazáshoz.
    def __init__(self):
        super().__init__()
        # EN: Buffers/holders (not all are used everywhere).
        # HU: Pufferek/tárolók (nem mind használatos mindenhol).
        self.date = []
        self.target_price = []
        self.price = []
        self.name = []
        # EN: Connection and cursor placeholders.
        # HU: Kapcsolat és kurzor helyőrzők.
        self.conn = None
        self.cursor = None
        # EN: Default flag whether a product is watched.
        # HU: Alapértelmezett jelző, hogy a termék megfigyelt-e.
        self.watched = True
        # EN: Collected product_ids for “checked” items.
        # HU: „checked” tételek product_id gyűjteménye.
        self.listed = []
        # EN: Timestamp string used in exports (FS-friendly format).
        # HU: Időbélyeg sztring exportokhoz (fájlrendszerbarát formátum).
        self.date = datetime.now().strftime("%Y/%m/%d %H:%M:%S").replace("/", "_").replace(":", "-")
        # EN: Default export path: current user's Desktop.
        # HU: Alapértelmezett export útvonal: a felhasználó Asztala.
        self.path = os.path.join(os.environ["USERPROFILE"], "Desktop")

    def connect(self):
        # EN: Open DB connection, enable FK checks, create tables if missing.
        # HU: Adatbázis-kapcsolat megnyitása, FK ellenőrzés bekapcsolása, táblák létrehozása ha hiányoznak.
        try:
            self.conn = sqlite3.connect('pricechecker.db')
            self.cursor = self.conn.cursor()
            # EN: Enforce foreign key constraints on this connection.
            # HU: Idegen kulcs megszorítások érvényesítése ezen a kapcsolaton.
            self.cursor.execute("PRAGMA foreign_keys = ON")
            # EN: Main products table; product_id is a unique business key.
            # HU: Fő products tábla; a product_id egyedi üzleti kulcs.
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER UNIQUE NOT NULL, product_name TEXT, price REAL, target_price REAL, comment TEXT, date DATETIME, checked BOOLEAN)")
            # EN: Price log table; FK references products.product_id (UNIQUE).
            # HU: Árnapló tábla; FK a products.product_id (UNIQUE) oszlopra mutat.
            self.cursor.execute(
                "CREATE TABLE IF NOT EXISTS price_log (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, price REAL, date DATETIME, FOREIGN KEY(product_id) REFERENCES products(product_id) ON DELETE CASCADE)")
        except sqlite3.OperationalError as e:
            # EN: Display DB-level operational errors.
            # HU: Adatbázis szintű operációs hibák megjelenítése.
            messagebox.showerror("Error", e)

    def add_to_db(self, product_id, product_name, product_price, target_price, comment, date, watched):
        # EN: Insert a single product row into products.
        # HU: Egy terméksor beszúrása a products táblába.
        try:
            self.cursor.execute(
                "INSERT INTO products (product_id, product_name, price, target_price, comment, date, checked) VALUES (?,?,?,?,?,?,?)",
                (product_id, product_name, product_price, target_price, comment, date, watched)
            )
            self.conn.commit()

        except Exception as e:
            # EN: Non-fatal warning dialog on insert failure.
            # HU: Nem végzetes figyelmeztetés beszúrási hiba esetén.
            messagebox.showwarning("Figyelem!", f"Hiba történt!\n{e}")

    def is_checked(self):
        # EN: Collect product_ids where “checked” flag is 1.
        # HU: product_id-k összegyűjtése, ahol a „checked” jelző 1.
        self.cursor.execute("SELECT product_id FROM products WHERE checked=1")
        checked = self.cursor.fetchall()
        for i in checked:
            self.listed.append(i[0])
        return self.listed

    def query(self):
        # EN: Fetch all product rows.
        # HU: A products tábla összes sorának lekérdezése.
        self.cursor.execute("SELECT * FROM products")
        queried = self.cursor.fetchall()
        return queried

    def delete_one(self, select):
        # EN: Delete a single product by internal row id (PK).
        # HU: Egy termék törlése belső sorazonosító (PK) alapján.
        self.cursor.execute("DELETE FROM products WHERE id=?", (select,))
        self.conn.commit()

    def delete_all(self):
        # EN: Delete all products; also clear collected list.
        # HU: Minden termék törlése; a gyűjtött lista ürítése is.
        self.cursor.execute("DELETE FROM products")
        self.conn.commit()
        self.listed = []

    def query_product_id(self, db_id):
        # EN: Map internal row id (PK) → business product_id.
        # HU: Belső sorazonosítóból (PK) üzleti product_id lekérése.
        self.cursor.execute("SELECT product_id FROM products WHERE id=?", (db_id,))
        product_id = self.cursor.fetchone()
        return product_id

    def update_date(self, date, db_id):
        # EN: Update last-checked timestamp for a product row.
        # HU: A terméksor utolsó ellenőrzésének idejét frissíti.
        self.cursor.execute("UPDATE products SET date=? WHERE id=?", (date, db_id))
        self.conn.commit()

    def update(self, target_price, comment, db_id):
        # EN: Update target price and comment for a row.
        # HU: Célár és megjegyzés frissítése egy soron.
        self.cursor.execute(
            "UPDATE products SET target_price=?, comment=? WHERE id=?",
            (target_price, comment, db_id)
        )
        self.conn.commit()

    def add_to_log(self, product_id, price, date):
        # EN: Append one entry into the price history log.
        # HU: Egy bejegyzés hozzáfűzése az árnaplóhoz.
        self.cursor.execute(
            "INSERT INTO price_log (product_id, price, date) VALUES (?,?,?)",
            (product_id, price, date)
        )
        self.conn.commit()

    def log_query_all(self):
        # EN: Export full price_log (product_id, price, date) into a CSV on Desktop.
        # HU: A teljes price_log exportálása (product_id, price, date) CSV-be az Asztalra.
        self.cursor.execute("SELECT product_id, price, date FROM price_log ORDER BY product_id")
        selected = self.cursor.fetchall()
        try:
            with open(f"{self.path}/Export-{self.date}.csv", 'w', newline='') as csvfile:
                fieldnames = ['product_id', 'price', 'date']
                csvwriter = csv.writer(csvfile, delimiter='|')
                for i in selected:
                    # EN: Write header then the row (per iteration).
                    # HU: Fejléc, majd a sor kiírása (iterációnként).
                    csvwriter.writerow(fieldnames)
                    csvwriter.writerow(i)
            messagebox.showinfo("", "Sikeres exportálás!")
        except Exception as e:
            # EN: Report file I/O errors on export.
            # HU: Fájlműveleti hiba jelentése export közben.
            messagebox.showerror("Hiba", f"Hiba az exportálásnál! \n {e}")

    def log_query(self, filename, product_id):
        # EN: Export price_log filtered to a specific product_id; file name suffix provided.
        # HU: price_log export adott product_id-re szűrve; a fájlnév végződését a paraméter adja.
        self.cursor.execute(
            "SELECT product_id, price, date FROM price_log WHERE product_id=? ORDER BY date",
            (product_id,)
        )
        selected = self.cursor.fetchall()
        filename = filename
        try:
            with open(f'{self.path}/Export-{filename}-{self.date}.csv', 'w', newline='') as csvfile:
                fieldnames = ['product_id', 'price', 'date']
                csvwriter = csv.writer(csvfile, delimiter='|')
                for i in selected:
                    # EN: Write header then the row (per iteration).
                    # HU: Fejléc, majd a sor kiírása (iterációnként).
                    csvwriter.writerow(fieldnames)
                    csvwriter.writerow(i)
            messagebox.showinfo("", "Sikeres exportálás!")
        except Exception as e:
            # EN: Report file I/O errors on export.
            # HU: Fájlműveleti hiba jelentése export közben.
            messagebox.showerror("Hiba", f"Hiba az exportálásnál! \n {e}")

    def close(self):
        # EN: Gracefully close DB resources if they exist.
        # HU: DB erőforrások szabályos lezárása, ha léteznek.
        if self.cursor and self.conn:
            self.cursor.close()
            self.conn.close()
