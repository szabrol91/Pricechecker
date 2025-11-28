import datetime
from tkinter import ttk, messagebox
import customtkinter
from tkinter import *
from datetime import datetime
from misc import Api, Screen


class CheckedProducts(customtkinter.CTkFrame):
    def __init__(self, master, database, **kwargs):
        # EN: Initialize CTkFrame and store shared database handle.
        # HU: CTkFrame inicializálása és a megosztott adatbázis példány eltárolása.
        super().__init__(master, **kwargs)
        self.database = database
        # EN: Initial query to populate the table.
        # HU: Kezdeti lekérdezés a tábla feltöltéséhez.
        self.queried = self.database.query()
        # EN: Per-column sort direction toggles.
        # HU: Oszloponkénti rendezési irány tárolása.
        self.sort_dir = {}

        # EN: Create Treeview with 6 data columns (no implicit "#0" column).
        # HU: Treeview létrehozása 6 adat-oszloppal (implicit „#0” nélkül).
        self.chkd_table = ttk.Treeview(
            self, columns=("c1", "c2", "c3", "c4", "c5", "c6"), show="headings",
        )
        # EN: Column geometry and behavior.
        # HU: Oszlopok méretezése és viselkedése.
        self.chkd_table.column("c1", anchor=CENTER, stretch=NO, width=450, minwidth=450)
        self.chkd_table.column("c2", anchor=CENTER, stretch=NO, width=100, minwidth=100)
        self.chkd_table.column("c3", anchor=CENTER, stretch=NO, width=100, minwidth=100)
        self.chkd_table.column("c4", anchor=CENTER, stretch=NO, width=125, minwidth=125)
        self.chkd_table.column("c5", anchor=CENTER, stretch=NO, width=125, minwidth=125)
        # EN: Hidden column (e.g., internal DB id).
        # HU: Rejtett oszlop (pl. belső DB azonosító).
        self.chkd_table.column("c6", anchor=CENTER, stretch=NO, width=0, minwidth=0)

        # EN: Headings with clickable sort callbacks.
        # HU: Fejlécek kattintható rendezési callback-kel.
        self.chkd_table.heading("c1", text="Termék neve",       command=lambda c="c1": self.sorting(self.chkd_table, c))
        self.chkd_table.heading("c2", text="Termék ára",        command=lambda c="c2": self.sorting(self.chkd_table, c))
        self.chkd_table.heading("c3", text="Célár",             command=lambda c="c3": self.sorting(self.chkd_table, c))
        self.chkd_table.heading("c4", text="Megjegyzés",        command=lambda c="c4": self.sorting(self.chkd_table, c))
        self.chkd_table.heading("c5", text="Utolsó frissítés",  command=lambda c="c5": self.sorting(self.chkd_table, c))
        # EN: Hidden heading (kept for column alignment).
        # HU: Rejtett fejléc (az oszlop igazítás megőrzésére).
        self.chkd_table.heading("c6")
        self.chkd_table.pack(fill="both", ipady=50)

        # EN: Block header-resize interactions (no manual column resizing).
        # HU: Fejléc-átméretezés tiltása (kézi oszlopszélesség állítás letiltva).
        self.chkd_table.bind("<Button-1>", self.block_resize)
        self.chkd_table.bind("<B1-Motion>", self.block_resize)
        self.chkd_table.bind("<Double-Button-1>", self.block_resize)

        # EN: Initial fill from query results.
        # HU: Kezdeti feltöltés a lekérdezés eredményével.
        self.build_chkd_table(self.queried)

    def block_resize(self, event):
        # EN: If pointer is over a header separator, swallow the event.
        # HU: Ha az egér a fejléc elválasztóján van, az esemény megszakítása.
        if self.chkd_table.identify_region(event.x, event.y) == "separator":
            return "break"
        return None

    def sorting(self, chkd_table, col):
        # EN: Generic sorting by the given column.
        # HU: Általános rendezés a megadott oszlop szerint.
        def keyfunc(iid):
            # EN: Raw cell value for sorting.
            # HU: Nyers cellaérték a rendezéshez.
            raw = chkd_table.set(iid, col)
            if col in {"c1"}:
                # EN: Try numeric compare, fallback to string.
                # HU: Próbáljuk számmá alakítani, különben stringként rendezzük.
                try:
                    return int(raw)
                except ValueError:
                    return raw
            elif col in {"c3"}:
                # EN: Try float compare, fallback to string.
                # HU: Próbáljuk lebegőpontos számmá alakítani, különben string.
                try:
                    return float(raw)
                except ValueError:
                    return raw
            # EN: Default case: case-insensitive lexicographic.
            # HU: Alapeset: kisbetűs, lexikografikus rendezés.
            return raw.lower()

        # EN: Toggle current sort direction for this column.
        # HU: Az aktuális oszlop rendezési irányának váltása.
        reverse = self.sort_dir.get(col, False)

        # EN: Collect and sort row iids by the key function.
        # HU: Sorok iidek összegyűjtése és rendezése a kulcsfüggvénnyel.
        items = list(chkd_table.get_children(""))
        items.sort(key=keyfunc, reverse=reverse)

        # EN: Reorder rows in the Treeview.
        # HU: Sorok átrendezése a Treeview-ban.
        for idx, iid in enumerate(items):
            chkd_table.move(iid, "", idx)

        # EN: Store next direction (toggle).
        # HU: Következő kattintásra ellentétes irányt tárolunk.
        self.sort_dir[col] = not reverse

        # EN: Rebind header command to keep sorting behavior consistent.
        # HU: Fejléc callback újrakötése a rendezési viselkedés megőrzéséhez.
        chkd_table.heading(col, command=lambda c=col: self.sorting(chkd_table, c))

    def build_chkd_table(self, queried):
        # EN: Clear table and configure row striping tags.
        # HU: Tábla ürítése és sorkiemelési tagek beállítása.
        self.chkd_table.delete(*self.chkd_table.get_children())
        self.chkd_table.tag_configure("odd", background="white")
        self.chkd_table.tag_configure("even", background="light blue")

        # EN: Insert rows; c6 holds DB id from query[0].
        # HU: Sorok beszúrása; a c6 oszlopban a DB azonosító (query[0]) van.
        iid = 0
        for query in queried:
            if iid % 2 == 0:
                self.chkd_table.insert(
                    parent="", index="end", iid=iid,
                    values=(query[2], query[3], query[4], query[5], query[6], query[0]),
                    tags=("odd",),
                )
            else:
                self.chkd_table.insert(
                    parent="", index="end", iid=iid,
                    values=(query[2], query[3], query[4], query[5], query[6], query[0]),
                    tags=("even",),
                )
            iid += 1


class CheckedProductsActivities(customtkinter.CTkFrame, Api):
    def __init__(self, master, database, table_frame: CheckedProducts, **kwargs):
        # EN: Action panel with access to the table and API.
        # HU: Akciópanel a táblához és az API-hoz való hozzáféréssel.
        super().__init__(master, **kwargs)
        self.toplevel_window = None
        self.items = None
        self.selected = None

        # EN: Data providers and references.
        # HU: Adatszolgáltatók és hivatkozások.
        self.api = Api()
        self.products = self.api.products
        self.database = database
        self.table_frame = table_frame
        self.chkd_table = table_frame.chkd_table

        # EN: Buttons layout.
        # HU: Gombok elrendezése.
        self.delete_one_btn = customtkinter.CTkButton(
            self, text="Töröl", hover_color="red", state=DISABLED, command=self.delete_one
        )
        self.delete_one_btn.grid(row=0, column=0, padx=(50, 10), pady=25)

        self.delete_all_btn = customtkinter.CTkButton(
            self, text="Mindent töröl", hover_color="red", command=self.delete_all
        )
        self.delete_all_btn.grid(row=0, column=1, padx=10, pady=25)

        self.pricecheck_one_btn = customtkinter.CTkButton(
            self, text="Ár ellenőrzés", hover_color="green", state=DISABLED, command=self.pricecheck_one
        )
        self.pricecheck_one_btn.grid(row=0, column=2, padx=10, pady=25)

        self.pricecheck_all_btn = customtkinter.CTkButton(
            self, text="Minden ár ellenőrzése", hover_color="green", command=self.pricecheck_all
        )
        self.pricecheck_all_btn.grid(row=0, column=3, padx=10, pady=25)

        # EN: Selection and double-click bindings.
        # HU: Kijelölés és dupla kattintás eseménykötések.
        self.chkd_table.bind("<<TreeviewSelect>>", lambda _e: self.selection())
        self.chkd_table.bind("<Double-Button-1>", lambda *_: self.open_toplevel(), add="+")

    def open_toplevel(self):
        # EN: Open editor toplevel or focus existing window.
        # HU: Szerkesztő toplevel megnyitása, vagy a meglévő fókuszba hozása.
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(
                master=self, api=self.api, database=self.database, table_frame=self.table_frame
            )
        else:
            self.toplevel_window.focus()

    def selection(self):
        # EN: Cache selected row iids; enable buttons if selection exists.
        # HU: Kijelölt sorok iidek eltárolása; gombok engedélyezése ha van kijelölés.
        self.selected = self.chkd_table.selection()
        if self.selected:
            self.delete_one_btn.configure(state=NORMAL)
            self.pricecheck_one_btn.configure(state=NORMAL)

    def delete_one(self):
        # EN: Delete selected entries from DB and view.
        # HU: Kijelölt elemek törlése az adatbázisból és a nézetből.
        popup = messagebox.askyesno("Termék törlése", "Biztosan törölni akarod a terméket?")
        if popup == 1:
            for select in self.selected:
                # EN: DB id stored in hidden column c6 (index 5).
                # HU: A DB azonosító a rejtett c6 oszlopban van (5-ös index).
                db_id = self.chkd_table.item(select, "values")[5]
                self.database.delete_one(db_id)
                self.chkd_table.delete(select)
                self.delete_one_btn.configure(state=DISABLED)

    def delete_all(self):
        # EN: Wipe table and delete all rows from DB.
        # HU: Tábla kiürítése és minden sor törlése az adatbázisból.
        popup = messagebox.askyesno("Termékek törlése", "Biztosan törölni akarod a termékeket?")
        if popup == 1:
            self.chkd_table.delete(*self.chkd_table.get_children())
            self.database.delete_all()

    def pricecheck_one(self):
        # EN: Price check for selected items; log and update last-checked timestamp.
        # HU: Kijelölt tételek ár-ellenőrzése; naplózás és az utolsó ellenőrzés idejének frissítése.
        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        for select in self.selected:
            db_id = int(self.chkd_table.item(select, "values")[5])
            product_id = self.database.query_product_id(db_id)
            # EN: Iterate over returned product ids (as provided by the DB layer).
            # HU: A DB réteg által adott product_id-ken iterálunk.
            for ids in product_id:
                for product in self.products:
                    if product["id"] == ids:
                        product_id = self.database.query_product_id(db_id)
                        for prod_id in product_id:
                            pid = prod_id
                        # EN: Append to price log (current price, timestamp).
                        # HU: Árnapló bővítése (aktuális ár, időbélyeg).
                        self.database.add_to_log(pid, self.chkd_table.item(select, "values")[1], date)
                        # EN: Compare live price to target; notify and update timestamp.
                        # HU: Élő ár összevetése a célárral; értesítés és időbélyeg frissítés.
                        if product["price"] <= float(self.chkd_table.item(select, "values")[2]):
                            product_name = self.chkd_table.item(select, "values")[0]
                            messagebox.showinfo("Figyelem!", f"A termék ára lecsökkent!\n {product_name}")
                            self.database.update_date(date, db_id)
                        else:
                            self.database.update_date(date, db_id)
                        # EN: Refresh table view from DB.
                        # HU: Tábla frissítése az adatbázisból.
                        self.table_frame.build_chkd_table(self.database.query())

    def pricecheck_all(self):
        # EN: Price check across all rows; update timestamps and extend log.
        # HU: Ár-ellenőrzés az összes soron; időbélyeg frissítése és napló bővítése.
        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        for i in self.chkd_table.get_children():
            db_ids = self.chkd_table.item(i, "values")[5]
            product_ids = self.database.query_product_id(db_ids)
            for ids in product_ids:
                for product in self.products:
                    if product["id"] == ids:
                        self.database.update_date(date, db_ids)
                        product_id = self.database.query_product_id(db_ids)
                        for prod_id in product_id:
                            pid = prod_id
                        self.database.add_to_log(pid, self.chkd_table.item(i, "values")[1], date)
                        if product["price"] <= float(self.chkd_table.item(i, "values")[2]):
                            product_name = self.chkd_table.item(i, "values")[0]
                            messagebox.showinfo("Figyelem!", f"A termék ára lecsökkent! \n{product_name}")
                        self.table_frame.build_chkd_table(self.database.query())


class ToplevelWindow(customtkinter.CTkToplevel, Screen):
    def __init__(self, master, api, table_frame: CheckedProducts, database, **kwargs):
        # EN: Popup editor window for editing target price/comment of the selected row.
        # HU: Felugró szerkesztő ablak a kijelölt sor célárának/megjegyzésének módosításához.
        super().__init__(master, **kwargs)
        self.title("Módosítás")
        # EN: Set window geometry using Screen helper.
        # HU: Ablakgeometria beállítása a Screen segédosztállyal.
        Screen(self, 400, 400)
        self.table_frame = table_frame
        self.chkd_table = table_frame.chkd_table
        # EN: Currently selected row (iid) and its values snapshot.
        # HU: Jelenleg kijelölt sor (iid) és az értékeinek pillanatképe.
        self.selected = self.chkd_table.selection()[0]
        self.selected_item = self.chkd_table.item(self.selected, "values")
        self.database = database
        self.api = api
        self.products = api.products

        # EN: Header label and current price display.
        # HU: Fejléc címke és aktuális ár megjelenítése.
        self.toplevel_label = customtkinter.CTkLabel(self, fg_color="transparent", text=self.selected_item[0])
        self.toplevel_label.pack(padx=10, pady=10)
        self.price_label = customtkinter.CTkLabel(self, fg_color="transparent", text=self.selected_item[1])
        self.price_label.pack(padx=10, pady=10)

        # EN: Editors with placeholders set from current values.
        # HU: Szerkesztők a jelenlegi értékeket mutató placeholderrel.
        self.target_entry = customtkinter.CTkEntry(self, placeholder_text=self.selected_item[2])
        self.target_entry.pack(padx=10, pady=10)

        if self.selected_item[3]:
            self.comment_entry = customtkinter.CTkEntry(self, placeholder_text=self.selected_item[3])
        else:
            self.comment_entry = customtkinter.CTkEntry(self, placeholder_text="Megjegyzés(opcionális)")
        self.comment_entry.pack(padx=10, pady=10)

        # EN: Save button (updates DB then closes).
        # HU: Mentés gomb (DB frissítés, majd ablak bezárása).
        self.update_btn = customtkinter.CTkButton(self, text="Frissít", hover_color="green", command=self.update_checked)
        self.update_btn.pack(padx=10, pady=10)

    def update_checked(self):
        # EN: Validate new target price, update DB, refresh view, close window.
        # HU: Új célár ellenőrzése, DB frissítés, nézet frissítése, ablak bezárása.
        new_target_price = self.target_entry.get().replace(",", ".")
        if new_target_price.replace(".", "").isdigit() and float(new_target_price):
            self.database.update(new_target_price, self.comment_entry.get(), self.selected_item[5])
            messagebox.showinfo("", "A célárat és/vagy a megjegyzést frissítetted")
            self.table_frame.build_chkd_table(self.database.query())
            self.destroy()
        else:
            messagebox.showerror("Hiba", "A célár csak pozitív szám lehet!")
