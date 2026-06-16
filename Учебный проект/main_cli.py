import argparse
import sys
from database import DatabaseManager
from data_export import DataExporter
from logger_config import setup_logger

logger = setup_logger("CLI")


def main():
    parser = argparse.ArgumentParser(description="Система управления доставкой")
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Отчеты
    report_parser = subparsers.add_parser("report", help="Показать отчет")
    report_parser.add_argument("--period", choices=["day", "week", "month"], default="month", help="Период отчета")

    # Экспорт
    export_parser = subparsers.add_parser("export", help="Экспорт заказов")
    export_parser.add_argument("--file", required=True, help="Имя файла (XML или JSON)")

    # Импорт
    import_parser = subparsers.add_parser("import", help="Импорт заказов")
    import_parser.add_argument("--file", required=True, help="Имя файла (XML или JSON)")

    # Добавить клиента
    add_cust_parser = subparsers.add_parser("add-customer", help="Добавить нового клиента")
    add_cust_parser.add_argument("--name", required=True, help="Имя клиента")
    add_cust_parser.add_argument("--phone", default="", help="Телефон")
    add_cust_parser.add_argument("--address", default="", help="Адрес")

    # Удалить клиента
    delete_cust_parser = subparsers.add_parser("delete-customer", help="Удалить клиента")
    delete_cust_parser.add_argument("--id", type=int, required=True, help="ID клиента")

    args = parser.parse_args()
    db = DatabaseManager()
    exporter = DataExporter(db)

    if args.command == "report":
        report = db.get_report(args.period)
        print(f"\n--- Отчет за {args.period} ---")
        print(f"Заказы по статусам: {report['status_counts']}")
        print(f"Топ-3 клиента: {report['top_clients']}")
        print(f"Выручка: {report['revenue']} руб.\n")

    elif args.command == "export":
        if args.file.endswith(".json"):
            exporter.export_json(args.file)
            print(f"Экспорт в {args.file} выполнен успешно")
        elif args.file.endswith(".xml"):
            exporter.export_xml(args.file)
            print(f"Экспорт в {args.file} выполнен успешно")
        else:
            print("Ошибка: Поддерживаются только .json и .xml")
            sys.exit(1)

    elif args.command == "import":
        if args.file.endswith(".json"):
            exporter.import_json(args.file)
            print(f"Импорт из {args.file} выполнен успешно")
        elif args.file.endswith(".xml"):
            exporter.import_xml(args.file)
            print(f"Импорт из {args.file} выполнен успешно")
        else:
            print("Ошибка: Поддерживаются только .json и .xml")
            sys.exit(1)

    elif args.command == "add-customer":
        from models import Customer
        customer = Customer(name=args.name, phone=args.phone, address=args.address)
        cust_id = db.add_customer(customer)
        print(f"Клиент '{args.name}' успешно добавлен с ID: {cust_id}")

    elif args.command == "delete-customer":
        from models import Customer

        customers = db.get_customers()
        customer = next((c for c in customers if c.id == args.id), None)

        if not customer:
            print(f"Клиент с ID {args.id} не найден!")
            print("\nСписок доступных клиентов:")
            for c in customers:
                print(f"   ID: {c.id} | {c.name} | {c.phone or 'без телефона'}")
            sys.exit(1)

        print(f"\nИнформация о клиенте:")
        print(f"   ID: {customer.id}")
        print(f"   Имя: {customer.name}")
        print(f"   Телефон: {customer.phone or 'не указан'}")
        print(f"   Адрес: {customer.address or 'не указан'}")

        orders = db.get_orders()
        customer_orders = [o for o in orders if o.customer_id == args.id]

        if customer_orders:
            print(f"\nУ клиента есть {len(customer_orders)} заказ(ов):")
            for order in customer_orders:
                print(
                    f"   - Заказ #{order.id} от {order.order_date} | Статус: {order.status} | Сумма: {order.total} руб.")
            print("\nУдаление невозможно: существуют связанные заказы.")
            print("Сначала удалите все заказы этого клиента.")
            sys.exit(1)

        confirm = input(f"\nВведите ID клиента ({args.id}) для подтверждения удаления: ")
        if confirm.strip() != str(args.id):
            print("ID не совпадает. Удаление отменено.")
            sys.exit(1)

        if db.delete_customer(args.id):
            print(f"Клиент '{customer.name}' (ID: {args.id}) успешно удален.")
        else:
            print("Не удалось удалить клиента.")
            sys.exit(1)

    else:
        parser.print_help()
        print("\nПримеры использования:")
        print("   python main_cli.py report --period month")
        print("   python main_cli.py add-customer --name 'Иван Иванов' --phone '+79991234567'")
        print("   python main_cli.py delete-customer --id 5")
        print("   python main_cli.py export --file orders.json")
        print("   python main_cli.py import --file orders.xml")


if __name__ == "__main__":
    main()