from datetime import datetime
from tkinter import ttk
import customtkinter
from tkinter import *
from database import Database
from tkinter import messagebox
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from checked_products import CheckedProducts, CheckedProductsActivities
from misc import Api, Screen
from PIL import Image
import schedule, time, threading

class MainWindow(customtkinter.CTk, Screen):
    def __init__(self):
        # EN: Initialize CTk root window; set title, size policy, colors.
        # HU: CTk főablak inicializálása; cím, méretkezelés, színek beállítása.
        super().__init__()
        self.title("Árfigyelő")
        self.resizable(False, False)
        self.configure(fg_color="#e9e9e9")

        # EN: Open DB connection and create menu bar.
        # HU: Adatbázis-kapcsolat megnyitása és menüsor létrehozása.
        self.database = Database()
        self.database.connect()
        self.menubar = CTkMenuBar(master=self, bg_color="#e9e9e9")
        self.menubar.pack(side="top", fill="x")

        # EN: Main product table frame and search/filter frame.
        # HU: Fő terméktábla-keret és kereső/szűrő keret.
        self.treeview_frame = TreeviewFrame(master=self, database=self.database, fg_color="transparent")
        self.treeview_frame.pack(fill="both", expand=True)
        self.searchandfilter_frame = SearchAndFilter(master=self, table_frame=self.treeview_frame, fg_color="transparent")
        self.searchandfilter_frame.pack(fill="both")

        # EN: Checked-products view and its actions panel.
        # HU: Megfigyelt termékek nézet és a hozzá tartozó műveleti panel.
        self.checked_products_frame = CheckedProducts(master=self, database=self.database, fg_color="transparent")
        self.checked_products_activities_frame = CheckedProductsActivities(master=self, database=self.database, table_frame=self.checked_products_frame, fg_color="transparent")

        # EN: Toplevel windows (lazy-created).
        # HU: Felugró ablakok (lusta létrehozással).
        self.export_toplevel_window = None
        self.help_toplevel_window = None

        # EN: Help icon image for the Help menu.
        # HU: Súgó menü ikonképe.
        self.question_mark = customtkinter.CTkImage(Image.open("question_mark.png"), size=(15,15))
        # EN: Position/size helper invocation.
        # HU: Pozíció/méret segédfüggvény meghívása.
        Screen(self, 725, 500)

        # EN: Top-level menus.
        # HU: Fő menüpontok.
        self.file_button = self.menubar.add_cascade("Fájl")
        self.export_button = self.menubar.add_cascade("Exportálás")
        self.help_button = self.menubar.add_cascade(image=self.question_mark, text="", postcommand=self.help, hover=False)
        self.help_button.grid(padx=(570,0))

        # EN: File menu entries.
        # HU: Fájl menü elemei.
        self.file_menu = CustomDropdownMenu(widget=self.file_button)
        self.file_menu.add_option(option="Összes termék", command=lambda: main_window())
        self.file_menu.add_option(option="Megfigylet termékek", command=lambda: checked_products())
        self.file_menu.add_separator()
        self.file_menu.add_option(option="Kilépés", command=self.quit)

        # EN: Export menu entries.
        # HU: Export menü elemei.
        self.export_menu = CustomDropdownMenu(widget=self.export_button)
        self.export_menu.add_option(option="Összes termék", command= self.database.log_query_all)
        self.export_menu.add_option(option="Kiválasztott termék", command=self.export_one)

        # EN: Helper to destroy current content frames before switching views.
        # HU: Segédfüggvény a jelenlegi keretek törléséhez nézetváltás előtt.
        def frame_destroy():
            self.treeview_frame.destroy()
            self.searchandfilter_frame.destroy()
            self.checked_products_frame.destroy()
            self.checked_products_activities_frame.destroy()

        # EN: Switch to main window (product list + search/filter).
        # HU: Váltás a fő nézetre (terméklista + kereső/szűrő).
        def main_window():
            frame_destroy()
            self.treeview_frame = TreeviewFrame(master=self,database=self.database, fg_color="transparent")
            self.treeview_frame.pack(fill="both", expand=True)
            self.searchandfilter_frame = SearchAndFilter(master=self, table_frame=self.treeview_frame, fg_color="transparent")
            self.searchandfilter_frame.pack(fill="both")

        # EN: Switch to checked-products view.
        # HU: Váltás a megfigyelt termékek nézetre.
        def checked_products():
            frame_destroy()
            self.checked_products_frame = CheckedProducts(master=self, database=self.database, fg_color="transparent")
            self.checked_products_frame.pack(fill="both", expand=True)
            self.checked_products_activities_frame = CheckedProductsActivities(master=self, database=self.database, table_frame=self.checked_products_frame, fg_color="transparent")
            self.checked_products_activities_frame.pack(fill="both", ipady=100)

    def export_one(self):
        # EN: Open the export dialog or focus it if already open.
        # HU: Export dialógus megnyitása vagy fókuszba hozása, ha már nyitva van.
        if self.export_toplevel_window is None or not self.export_toplevel_window.winfo_exists():
            self.export_toplevel_window = ExportToplevelWindow(self, database=self.database)
        else:
            self.export_toplevel_window.focus()

    def help(self):
        # EN: Open the help window or focus it if already open.
        # HU: Súgóablak megnyitása vagy fókuszba hozása, ha már nyitva van.
        if self.help_toplevel_window is None or not self.help_toplevel_window.winfo_exists():
            self.help_toplevel_window = HelpToplevelWindow(self)
        else:
            self.help_toplevel_window.focus()


class TreeviewFrame(customtkinter.CTkFrame, Api):
    def __init__(self, master, database, **kwargs):
        # EN: Frame with the main product table, bound to DB and API.
        # HU: Keret a fő terméktáblával, az adatbázishoz és API-hoz kötve.
        super().__init__(master, **kwargs)
        self.database = database
        self._textbox = None
        self.api = Api()
        self.products = self.api.products
        # EN: Create table and build initial content.
        # HU: Tábla létrehozása és kezdeti feltöltése.
        self.table = ttk.Treeview(self, columns=("c1", "c2", "c3", "c4", "c5"), show="headings", )
        self.build_table(self.products)
        self.sort_dir = {}
        self.toplevel_window = None

    def set_textbox(self, textbox):
        # EN: External textbox target to display product descriptions.
        # HU: Külső szövegdoboz beállítása termékleírás megjelenítéséhez.
        self._textbox = textbox

    def open_toplevel(self):
        # EN: Open watcher-assign toplevel for the selected product.
        # HU: Megfigyelésre felvétel felugró ablak megnyitása a kiválasztott termékhez.
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = ToplevelWindow(master=self, api=self.api, database=self.database,  table_frame=self)
        else:
            self.toplevel_window.focus()

    def toplevel_check(self):
        # EN: Only open toplevel if the selected product is not yet watched.
        # HU: Csak akkor nyit felugrót, ha a kijelölt termék még nincs megfigyelés alatt.
        watched = self.database.is_checked()
        selected = self.table.selection()
        selected_items = self.table.item(selected, "values")
        if int(selected_items[0]) in watched:
            pass
        else:
            self.open_toplevel()

    def build_table(self, products):
        # EN: Rebuild the table with the provided product list.
        # HU: A tábla újraépítése a megadott terméklistával.
        self.table.delete(*self.table.get_children())

        # EN: Column geometry and sorting header handlers.
        # HU: Oszlop-méretezés és rendező fejlécek.
        self.table.column("c1", anchor=CENTER, stretch=NO, width=75, minwidth=75)
        self.table.column("c2", anchor=CENTER, stretch=NO, width=500, minwidth=500)
        self.table.column("c3", anchor=CENTER, stretch=NO, width=100, minwidth=100)
        self.table.column("c4", anchor=CENTER, stretch=NO, width=150, minwidth=150)
        self.table.column("c5", anchor=CENTER, stretch=NO, width=75, minwidth=75)
        self.table.heading("c1", text="Termék ID", command=lambda c="c1": sorting(self.table, c))
        self.table.heading("c2", text="Termék neve", command=lambda c="c2": sorting(self.table, c))
        self.table.heading("c3", text="Termék ára", command=lambda c="c3": sorting(self.table, c))
        self.table.heading("c4", text="Kategória", command=lambda c="c4": sorting(self.table, c))
        self.table.heading("c5", text="Árfigyelés", command=lambda c="c5": sorting(self.table, c))

        # EN: Prevent manual column resize via header separators.
        # HU: Fejléc elválasztón keresztüli kézi oszlopszélesség-állítás tiltása.
        def block_resize(event):
            if self.table.identify_region(event.x, event.y) == "separator":
                return "break"
            return None

        # EN: Fill external description textbox from selection.
        # HU: Külső leírásmező feltöltése a kijelölt sor alapján.
        def description():
            if not self._textbox:
                return
            try:
                self.selected = self.table.selection()[0]
            except IndexError:
                self._textbox.configure(state="normal")
                self._textbox.delete("0.0", "end")
                self._textbox.configure(state="disabled")
                return
            selected_items = self.table.item(self.selected, "values")
            for product in products:
                if int(product["id"]) == int(selected_items[0]):
                    self._textbox.configure(state="normal")
                    self._textbox.delete("0.0", "end")
                    self._textbox.insert("0.0", product["description"])
                    self._textbox.configure(state="disabled")

        # EN: Bind interactions: block resize, update description, open toplevel on double-click.
        # HU: Eseménykötések: átméretezés tiltása, leírás frissítése, dupla kattintásra felugró nyitás.
        self.table.bind("<Button-1>", block_resize )
        self.table.bind("<B1-Motion>", block_resize)
        self.table.bind("<Double-Button-1>", block_resize)
        self.table.bind("<<TreeviewSelect>>", lambda _e: description())
        self.table.bind("<Double-Button-1>",lambda *_: self.toplevel_check(), add="+")
        self.table.pack(fill="both", expand=True)

        # EN: Row striping configuration.
        # HU: Sorok váltakozó háttérszínének beállítása.
        self.table.tag_configure("odd", background="white")
        self.table.tag_configure("even", background="light blue")

        # EN: Populate rows; last column shows watched status (check mark).
        # HU: Sorok feltöltése; utolsó oszlop a megfigyelési állapotot jelzi (pipa).
        iid = 0
        watched = self.database.is_checked()
        checked = "✔"
        unchecked = " "
        for product in products:
            if iid % 2 == 0:
                if product["id"] in watched:
                    self.table.insert(parent="", index="end", iid=iid, values=(product["id"], product["title"], product["price"], product["category"], checked), tags=("odd",))
                else:
                    self.table.insert(parent="", index="end", iid=iid,values=(product["id"], product["title"], product["price"], product["category"], unchecked), tags=("odd",))
            else:
                if product["id"] in watched:
                    self.table.insert(parent="", index="end", iid=iid, values=(product["id"], product["title"], product["price"], product["category"], checked), tags=("even",))
                else:
                    self.table.insert(parent="", index="end", iid=iid, values=(product["id"], product["title"], product["price"], product["category"], unchecked), tags=("even",))
            iid += 1

        # EN: Column-wise sorting helper bound to headings above.
        # HU: Az oszlopfejlécekhez kötött rendező segédfüggvény.
        def sorting(table, col):
            # EN: Compute sort key per row based on column and type.
            # HU: Rendezési kulcs előállítása soronként, oszloptól és típustól függően.
            def keyfunc(iid):
                raw = table.set(iid, col)
                if col in {"c1"}:
                    try:
                        return int(raw)
                    except ValueError:
                        return raw
                elif col in {"c3"}:
                    try:
                        return float(raw)
                    except ValueError:
                        return raw
                return raw.lower()

            # EN: Toggle sort direction and reorder items.
            # HU: Rendezési irány váltása és a tételek újrarendezése.
            reverse = self.sort_dir.get(col, False)
            items = list(table.get_children(""))
            items.sort(key=keyfunc, reverse=reverse)
            for idx, iid in enumerate(items):
                table.move(iid, "", idx)
            self.sort_dir[col] = not reverse
            table.heading(col, command=lambda c=col: sorting(table, c))

class ToplevelWindow(customtkinter.CTkToplevel, Screen):
    def __init__(self, master, api, table_frame, database, **kwargs):
        # EN: Popup to add the selected product to the watch list.
        # HU: Felugró ablak a kiválasztott termék megfigyelésre vételéhez.
        super().__init__(master, **kwargs)
        self.title("Termék megfigyelése")
        Screen(self, 400, 400)
        self.database = database
        self.api = api
        self.table = table_frame.table
        self.products = api.products
        self.selected = self.table.selection()[0]

        # EN: Labels for product title and current price.
        # HU: Címkék a termék nevéhez és aktuális árához.
        self.toplevel_label = customtkinter.CTkLabel(self, fg_color="transparent")
        self.toplevel_label.pack(padx=10, pady=10)
        self.price_label = customtkinter.CTkLabel(self, fg_color="transparent")
        self.price_label.pack(padx=10, pady=10)

        # EN: Inputs for target price and optional comment.
        # HU: Célár és opcionális megjegyzés beviteli mezők.
        self.target_entry = customtkinter.CTkEntry(self, placeholder_text="Írd be a célárat!")
        self.target_entry.pack(padx=10, pady=10)
        self.comment_entry = customtkinter.CTkEntry(self, placeholder_text="Megjegyzés(opcionális)")
        self.comment_entry.pack(padx=10, pady=10)

        # EN: Initialize labels based on the selected row.
        # HU: Címkék inicializálása a kijelölt sor alapján.
        selected_items = self.table.item(self.selected, "values")
        for product in self.products:
            if int(product["id"]) == int(selected_items[0]):
                self.toplevel_label.configure(text=product["title"])
                self.price_label.configure(text=product["price"])

        # EN: Watch toggle checkbox bound to a string variable ("1"/"0").
        # HU: Megfigyelés jelölőnégyzet, string változóhoz kötve („1”/„0”).
        check_var = customtkinter.StringVar(value="0")
        self.checkbox = customtkinter.CTkCheckBox(self, text="Árfigyelés",variable=check_var,
                                                  onvalue="1", offvalue="0",
                                                  corner_radius=0, checkbox_width=12, checkbox_height=12,
                                                  border_width=2, fg_color="green")
        self.checkbox.pack(padx=10, pady=10)

        # EN: Timestamp used when adding the record.
        # HU: Időbélyeg az adat felvételéhez.
        self.date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        # EN: Add-button handler: validates input and persists to DB.
        # HU: Hozzáadás gomb kezelő: ellenőrzi a bevitt adatot és rögzíti az adatbázisban.
        def add():
            if check_var.get() == "1" and self.target_entry.get():
                target_price = self.target_entry.get().replace(",", ".")
                floated = float(target_price)
                if target_price.replace(".", "").isdigit() and floated> 0:
                    self.database.add_to_db(selected_items[0], selected_items[1], selected_items[2], target_price, self.comment_entry.get(), self.date ,self.checkbox.get())
                    messagebox.showinfo("", "A termék felkerült a megfigyelt listára!")
                    table_frame.build_table(self.api.products)
                    self.destroy()
                else:
                    messagebox.showwarning("Figyelem!", "A célár csak pozitív szám lehet!")
                    self.focus()
            else:
                messagebox.showwarning("Figyelem!", "Minden mező kitöltése kötelező!")
                self.focus()

        self.add_button = customtkinter.CTkButton(self, text="Megfigyel", command=add)
        self.add_button.pack(padx=10, pady=10)

class SearchAndFilter(customtkinter.CTkFrame):
    def __init__(self, master, table_frame:TreeviewFrame, **kwargs):
        # EN: Search/filter panel bound to the main table.
        # HU: Kereső/szűrő panel, a fő táblához kötve.
        super().__init__(master, **kwargs)
        self.values = ["Összes"]
        self.api = Api()
        self.table_frame = table_frame
        # EN: Build category list (unique values).
        # HU: Kategórialista felépítése (egyedi értékek).
        for product in self.api.products:
            if product["category"] not in self.values:
                self.values.append(product["category"])

        # EN: Category combobox and label.
        # HU: Kategória-választó és címkéje.
        self.combobox_label = customtkinter.CTkLabel(self, text="Kategóriaválasztó:", fg_color="transparent")
        self.combobox_label.grid(row=0, column=0, padx=10, pady=10)

        self.combobox_var = customtkinter.StringVar(value=self.values[0])
        self.combobox = customtkinter.CTkComboBox(self, values=self.values, state="readonly", variable=self.combobox_var ,command=lambda *_: self.on_click())
        self.combobox.grid(row=0, column=1, padx=10, pady=10)

        # EN: Reset button to clear search or reload view.
        # HU: Visszaállítás gomb a keresés törléséhez vagy a nézet frissítéséhez.
        self.reset_button = customtkinter.CTkButton(self, text="Visszaállít", command= self.reset, hover_color="green")
        self.reset_button.grid(row=0, column=3)

        # EN: Search label/entry/button trio.
        # HU: Kereső címke/mező/gomb hármas.
        self.search_entry_label = customtkinter.CTkLabel(self, text="Kereső:", fg_color="transparent")
        self.search_entry_label.grid(row=1, column=0)

        self.search_entry = customtkinter.CTkEntry(self)
        self.search_entry.grid(row=1, column=1)
        self.search_entry.bind("<Return>", self.search)

        self.search_button = customtkinter.CTkButton(self, text="Keresés", command= self.search, hover_color="green")
        self.search_button.grid(row=1, column=3)

        # EN: Description area label and textbox; bind to TreeviewFrame.
        # HU: Leírás felirat és szövegdoboz; összekötve a TreeviewFrame-mel.
        self.description_textbox = customtkinter.CTkLabel(self, text="Leírás:", fg_color="transparent")
        self.description_textbox.grid(row=0, column=4)

        self.description_textbox = customtkinter.CTkTextbox(self, width=270, height=200, state="disabled", fg_color="transparent", wrap="word")
        self.description_textbox.insert("0.0", text="Hello")
        self.description_textbox.grid(row=1, column=4, padx=10, rowspan=100)
        table_frame.set_textbox(self.description_textbox)

    def reset(self):
        # EN: Reset search entry and refresh table.
        # HU: Keresőmező alaphelyzetbe és tábla frissítése.
        if self.search_entry.get() != "":
            self.search_entry.delete(0, "end")
            self.search()
        else:
            self.search()

    def search(self,event=None):
        # EN: Case-insensitive substring search on product titles.
        # HU: Kis/nagybetűt nem érzékeny részsztring-keresés a terméknevekben.
        searched = self.search_entry.get()
        filtered = [p for p in self.api.products if searched.lower() in p["title"].lower()]
        if filtered:
            self.table_frame.build_table(filtered)
            self.search_entry.delete(0, "end")
        else:
            messagebox.showwarning("Figyelem!", "Nincs ilyen termék az adatbátzisban!")
            self.search_entry.delete(0, "end")

    def on_click(self):
        # EN: Category change handler: filter table by selected category.
        # HU: Kategóriaváltás kezelése: tábla szűrése a választott kategóriára.
        selected = self.combobox.get()
        if selected == "Összes":
            self.table_frame.build_table(self.api.products)
        else:
            filtered = [p for p in self.api.products if p["category"] == selected]
            self.table_frame.build_table(filtered)

class ExportToplevelWindow(customtkinter.CTkToplevel, Screen):
    def __init__(self, master, database, **kwargs):
        # EN: Popup for exporting logs for all or selected product.
        # HU: Felugró ablak naplók exportálására minden vagy kiválasztott termékre.
        super().__init__(master, **kwargs)
        Screen(self, 400, 400)
        self.title("Export")
        self.database = database

        # EN: Choice mapping: product_name → product_id from DB query.
        # HU: Választási leképezés: product_name → product_id az adatbázisból.
        self.label = customtkinter.CTkLabel(self, text="Válaszd ki az exportálandó terméket")
        self.label.pack(padx=20, pady=20)
        self.choice_dict = {}
        self.choices = []
        self.queried = self.database.query()
        for queries in self.queried:
            self.choice_dict[queries[2]] = queries[1]
        for key in self.choice_dict.keys():
            self.choices.append(key)

        # EN: OptionMenu to pick a product by name.
        # HU: OptionMenu egy termék név szerinti kiválasztásához.
        self.optionmenu_var = customtkinter.StringVar(value=" ")
        self.optionmenu = customtkinter.CTkOptionMenu(self, variable=self.optionmenu_var, values=self.choices)
        self.optionmenu.pack(padx=20, pady=20)

        # EN: Export button triggers export_one with the chosen name.
        # HU: Export gomb az export_one hívására a kiválasztott névvel.
        self.export_button = customtkinter.CTkButton(self, text="Exportálás", command=lambda : self.export_one(self.optionmenu.get()))
        self.export_button.pack(padx=20, pady=20)
        self.export_button.pack(padx=20, pady=20)

    def export_one(self, choice):
        # EN: Resolve product_id from choice and export filtered log; close dialog.
        # HU: Termékazonosító kinyerése a választásból és szűrt napló exportálása; dialógus zárása.
        id = self.choice_dict.get(choice)
        self.database.log_query(choice, id)
        self.destroy()

class HelpToplevelWindow(customtkinter.CTkToplevel, Screen):
    def __init__(self, *args, **kwargs):
        # EN: Help window that displays contents of help.txt.
        # HU: Súgóablak, amely a help.txt tartalmát jeleníti meg.
        super().__init__(*args, **kwargs)
        self.title("Segítség")
        self.transient(self.master)
        self.lift()
        self.focus_set()
        self.after(0, lambda: (self.lift(), self.focus_force()))
        Screen(self, 400, 400)

        with open('help.txt', 'r', encoding='utf-8') as file:
            lines = file.read()

        self.help_textbox =  customtkinter.CTkTextbox(self, width=400, height=400, fg_color="transparent", wrap="word")
        self.help_textbox.insert("0.0", lines)
        self.help_textbox.configure(state="disabled")
        self.help_textbox.pack(padx=20, pady=20)

def scheduler_loop(app):
    # EN: Background scheduler: run daily at 00:00 Europe/Budapest on the GUI thread.
    # HU: Háttérütemező: minden nap 00:00-kor futtatás (Europe/Budapest) a GUI szálán.
    schedule.every().day.at("00:00", "Europe/Budapest").do(lambda: app.after(0, app.checked_products_activities_frame.pricecheck_all))
    while True:
        schedule.run_pending()
        time.sleep(0.5)

if __name__ == "__main__":
    # EN: Create app, start scheduler thread, enter TK main loop, then close DB.
    # HU: Alkalmazás létrehozása, ütemező szál indítása, TK főciklus, majd DB lezárása.
    root = MainWindow()
    threading.Thread(target=scheduler_loop, args=(root,), daemon=True).start()
    root.mainloop()
    root.database.close()
