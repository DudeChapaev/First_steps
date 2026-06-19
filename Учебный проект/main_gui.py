import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import DatabaseManager
from models import Customer, Order, OrderItem


class DeliveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Быстрая доставка - Управление заказами")
        self.root.geometry("950x600")
        self.db = DatabaseManager()

        self._create_widgets()
        self._load_orders()

    def _create_widgets(self):
        # Панель управления
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)

        # Кнопки управления клиентами
        ttk.Button(control_frame, text="Добавить клиента", command=self._add_customer_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Редактировать клиента", command=self._edit_customer_dialog).pack(side=tk.LEFT,
                                                                                                         padx=5)
        ttk.Button(control_frame, text="Удалить клиента", command=self._delete_customer_dialog).pack(side=tk.LEFT,
                                                                                                     padx=5)

        # Разделитель
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Кнопки управления заказами
        ttk.Button(control_frame, text="Добавить заказ", command=self._add_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Редактировать заказ", command=self._edit_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Удалить заказ", command=self._delete_order).pack(side=tk.LEFT, padx=5)

        # Фильтр и отчет
        ttk.Label(control_frame, text="Фильтр по статусу:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_var = tk.StringVar(value="")
        status_cb = ttk.Combobox(control_frame, textvariable=self.status_var,
                                 values=["", "новый", "в доставке", "выполнен", "отменён"], state="readonly", width=15)
        status_cb.pack(side=tk.LEFT, padx=5)
        status_cb.bind("<<ComboboxSelected>>", lambda e: self._load_orders())

        ttk.Button(control_frame, text="Показать отчёт", command=self._show_report).pack(side=tk.RIGHT, padx=5)

        # Таблица заказов
        columns = ("id", "date", "customer", "status", "total")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Дата")
        self.tree.heading("customer", text="Клиент")
        self.tree.heading("status", text="Статус")
        self.tree.heading("total", text="Сумма (руб)")

        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("date", width=100, anchor=tk.CENTER)
        self.tree.column("customer", width=250)
        self.tree.column("status", width=120, anchor=tk.CENTER)
        self.tree.column("total", width=120, anchor=tk.E)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _load_orders(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        orders = self.db.get_orders(status_filter=self.status_var.get() or None)
        for o in orders:
            self.tree.insert("", tk.END, iid=o.id,
                             values=(o.id, o.order_date, o.customer_name, o.status, f"{o.total:.2f}"))

    # === МЕТОДЫ УПРАВЛЕНИЯ КЛИЕНТАМИ ===

    def _add_customer_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый клиент")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Имя (обязательно):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Телефон:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        phone_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=phone_var, width=30).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Адрес:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        addr_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=addr_var, width=30).grid(row=2, column=1, padx=10, pady=5)

        def save_customer():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Имя клиента является обязательным полем!")
                return

            # Проверяем на дубликаты
            existing_customers = self.db.get_customers()
            if any(c.name.lower() == name.lower() for c in existing_customers):
                if not messagebox.askyesno("Дубликат", f"Клиент '{name}' уже существует. Добавить ещё одного?"):
                    return

            new_cust = Customer(name=name, phone=phone_var.get().strip(), address=addr_var.get().strip())
            self.db.add_customer(new_cust)
            messagebox.showinfo("Успех", f"Клиент '{name}' успешно добавлен в базу!")
            dialog.destroy()

        ttk.Button(dialog, text="Сохранить клиента", command=save_customer).grid(row=3, column=0, columnspan=2, pady=15)

    def _edit_customer_dialog(self):
        """Диалог выбора клиента для редактирования"""
        customers = self.db.get_customers()
        if not customers:
            messagebox.showinfo("Инфо", "Список клиентов пуст.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование клиента")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Выберите клиента для редактирования:", font=("Calibri", 10)).pack(padx=10, pady=15)

        customer_listbox = tk.Listbox(dialog, width=65, height=10, font=("Calibri", 9))
        customer_listbox.pack(padx=15, pady=5, fill=tk.X)

        orders = self.db.get_orders()

        for c in customers:
            customer_orders = [o for o in orders if o.customer_id == c.id]
            order_count = len(customer_orders)

            display_text = f"ID: {c.id} | {c.name}"
            if c.phone:
                display_text += f" | Тел: {c.phone}"
            if order_count > 0:
                display_text += f" | Заказов: {order_count}"

            customer_listbox.insert(tk.END, display_text)

        def open_edit():
            selection = customer_listbox.curselection()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите клиента из списка!")
                return

            selected_index = selection[0]
            customer = customers[selected_index]
            dialog.destroy()
            self._open_edit_customer_form(customer)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        edit_btn = tk.Button(
            button_frame,
            text="Редактировать",
            command=open_edit,
            width=15,
            height=1,
            font=("Calibri", 9)
        )
        edit_btn.pack(side=tk.LEFT, padx=15)

        cancel_btn = tk.Button(
            button_frame,
            text="Отмена",
            command=dialog.destroy,
            width=15,
            height=1,
            font=("Calibri", 9)
        )
        cancel_btn.pack(side=tk.LEFT, padx=15)

    def _open_edit_customer_form(self, customer: Customer):
        """Форма редактирования клиента с предзаполненными данными"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактирование клиента: {customer.name}")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Имя (обязательно):", font=("Calibri", 9)).grid(row=0, column=0, padx=10, pady=10,
                                                                                sticky=tk.W)
        name_var = tk.StringVar(value=customer.name)
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus()

        ttk.Label(dialog, text="Телефон:", font=("Calibri", 9)).grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        phone_var = tk.StringVar(value=customer.phone)
        ttk.Entry(dialog, textvariable=phone_var, width=30).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Адрес:", font=("Calibri", 9)).grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        addr_var = tk.StringVar(value=customer.address)
        ttk.Entry(dialog, textvariable=addr_var, width=30).grid(row=2, column=1, padx=10, pady=5)

        def update_customer():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Имя клиента является обязательным полем!")
                return

            # Проверяем на дубликаты (исключая текущего клиента)
            existing_customers = self.db.get_customers()
            duplicate = any(
                c.name.lower() == name.lower() and c.id != customer.id
                for c in existing_customers
            )
            if duplicate:
                if not messagebox.askyesno("Дубликат",
                                           f"Клиент '{name}' уже существует. Всё равно сохранить изменения?"):
                    return

            # Обновляем клиента
            updated_cust = Customer(
                id=customer.id,
                name=name,
                phone=phone_var.get().strip(),
                address=addr_var.get().strip()
            )

            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE customers SET name=?, phone=?, address=? WHERE id=?",
                    (updated_cust.name, updated_cust.phone, updated_cust.address, updated_cust.id)
                )

            messagebox.showinfo("Успех", f"Данные клиента '{name}' успешно обновлены!")
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="Сохранить изменения", command=update_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _delete_customer_dialog(self):
        customers = self.db.get_customers()
        if not customers:
            messagebox.showinfo("Инфо", "Список клиентов пуст.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Удаление клиента")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Выберите клиента для удаления:", font=("Calibri", 10)).pack(padx=10, pady=15)

        customer_listbox = tk.Listbox(dialog, width=65, height=10, font=("Calibri", 9))
        customer_listbox.pack(padx=15, pady=5, fill=tk.X)

        orders = self.db.get_orders()

        for c in customers:
            customer_orders = [o for o in orders if o.customer_id == c.id]
            order_count = len(customer_orders)

            display_text = f"ID: {c.id} | {c.name}"
            if c.phone:
                display_text += f" | Тел: {c.phone}"
            if order_count > 0:
                display_text += f" | Заказов: {order_count}"

            customer_listbox.insert(tk.END, display_text)

        def confirm_delete():
            selection = customer_listbox.curselection()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите клиента из списка!")
                return

            selected_index = selection[0]
            customer_id = customers[selected_index].id
            customer_name = customers[selected_index].name

            customer_orders = [o for o in orders if o.customer_id == customer_id]

            if customer_orders:
                messagebox.showerror(
                    "Невозможно удалить",
                    f"Клиент '{customer_name}' имеет {len(customer_orders)} заказ(ов).\n"
                    f"Удаление невозможно, пока существуют связанные заказы.\n\n"
                    f"Сначала удалите все заказы этого клиента."
                )
                return

            if messagebox.askyesno(
                    "Подтверждение",
                    f"Вы уверены, что хотите удалить клиента?\n\n"
                    f"Имя: {customer_name}\n"
                    f"ID: {customer_id}\n\n"
                    f"Это действие нельзя отменить!"
            ):
                if self.db.delete_customer(customer_id):
                    messagebox.showinfo("Успех", f"Клиент '{customer_name}' успешно удален.")
                    dialog.destroy()
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить клиента.")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        delete_btn = tk.Button(
            button_frame,
            text="Удалить",
            command=confirm_delete,
            width=15,
            height=1,
            font=("Calibri", 9)
        )
        delete_btn.pack(side=tk.LEFT, padx=15)

        cancel_btn = tk.Button(
            button_frame,
            text="Отмена",
            command=dialog.destroy,
            width=15,
            height=1,
            font=("Calibri", 9)
        )
        cancel_btn.pack(side=tk.LEFT, padx=15)

    # === МЕТОДЫ УПРАВЛЕНИЯ ЗАКАЗАМИ ===

    def _add_order(self):
        self._open_order_dialog()

    def _edit_order(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите заказ в таблице для редактирования")
            return
        order_id = int(selected[0])
        orders = self.db.get_orders()
        order = next((o for o in orders if o.id == order_id), None)
        if order:
            self._open_order_dialog(order)

    def _delete_order(self):
        selected = self.tree.selection()
        if not selected:
            return
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот заказ?"):
            self.db.delete_order(int(selected[0]))
            self._load_orders()

    def _open_order_dialog(self, order: Order = None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый заказ" if not order else "Редактирование заказа")
        dialog.geometry("550x450")
        dialog.transient(self.root)
        dialog.grab_set()

        customers = self.db.get_customers()
        if not customers:
            messagebox.showinfo("Инфо",
                                "Список клиентов пуст. Сначала добавьте клиента через кнопку 'Добавить клиента'.")
            dialog.destroy()
            return

        seen_names = set()
        unique_customers = []
        for c in customers:
            if c.name not in seen_names:
                seen_names.add(c.name)
                unique_customers.append(c)

        cust_names = [c.name for c in unique_customers]
        cust_map = {c.name: c.id for c in unique_customers}

        ttk.Label(dialog, text="Клиент:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        current_cust_name = next((c.name for c in unique_customers if c.id == order.customer_id), "") if order else \
        cust_names[0]
        cust_var = tk.StringVar(value=current_cust_name)
        cust_cb = ttk.Combobox(dialog, textvariable=cust_var, values=cust_names, state="readonly", width=35)
        cust_cb.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Дата (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d") if not order else order.order_date)
        ttk.Entry(dialog, textvariable=date_var, width=35).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Статус:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        status_var = tk.StringVar(value="новый" if not order else order.status)
        status_cb = ttk.Combobox(dialog, textvariable=status_var, values=["новый", "в доставке", "выполнен", "отменён"],
                                 state="readonly", width=35)
        status_cb.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Товары (Название, Кол-во, Цена через запятую,\nкаждый товар с новой строки):").grid(
            row=3, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)

        items_text = ""
        if order:
            items_text = "\n".join([f"{i.product_name}, {i.quantity}, {i.price}" for i in order.items])

        items_var = tk.Text(dialog, height=10, width=60)
        items_var.insert(tk.END, items_text)
        items_var.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        def save():
            try:
                cust_name = cust_var.get()
                customer_id = cust_map[cust_name]

                items = []
                total = 0.0
                for line in items_var.get("1.0", tk.END).splitlines():
                    if line.strip():
                        parts = line.split(",")
                        if len(parts) != 3:
                            raise ValueError("Неверный формат строки товара. Нужно: Название, Кол-во, Цена")
                        name = parts[0].strip()
                        qty = int(parts[1].strip())
                        price = float(parts[2].strip())
                        items.append(OrderItem(product_name=name, quantity=qty, price=price))
                        total += qty * price

                new_order = Order(
                    id=order.id if order else None,
                    customer_id=customer_id,
                    order_date=date_var.get(),
                    status=status_var.get(),
                    total=total,
                    items=items
                )

                if order:
                    self.db.update_order(new_order)
                else:
                    self.db.add_order(new_order)

                dialog.destroy()
                self._load_orders()
            except Exception as e:
                messagebox.showerror("Ошибка ввода", f"Проверьте формат данных:\n{e}")

        ttk.Button(dialog, text="Сохранить заказ", command=save).grid(row=5, column=0, columnspan=2, pady=15)

    def _show_report(self):
        report = self.db.get_report("month")
        report_win = tk.Toplevel(self.root)
        report_win.title("Отчет за текущий месяц")
        report_win.geometry("400x350")
        report_win.transient(self.root)

        text = f"Общая выручка: {report['revenue']:.2f} руб.\n\n"
        text += "Заказы по статусам:\n"
        for status, count in report['status_counts'].items():
            text += f"   • {status.capitalize()}: {count}\n"

        text += "\nТоп-3 клиента по сумме:\n"
        if not report['top_clients']:
            text += "   (Нет данных)\n"
        else:
            for i, client in enumerate(report['top_clients'], 1):
                text += f"   {i}. {client['name']}: {client['sum']:.2f} руб.\n"

        ttk.Label(report_win, text=text, justify=tk.LEFT, font=("Calibri", 10)).pack(padx=20, pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = DeliveryApp(root)
    root.mainloop()