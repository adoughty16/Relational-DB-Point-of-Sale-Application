import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def print_menu(cursor):
    # Print menu items and prices
    cursor.execute("SELECT dish_name, price FROM dishes")
    menu_items = cursor.fetchall()

    if not menu_items:
        print("No menu items found.")
    else:
        print("\nMenu Items and Prices:")
        for item in menu_items:
            print(f"{item[0]} - ${item[1]:.2f}")

def add_order(cursor):
    # Will prompt for Name, Item
    customer_name = input("Enter customer name: ")
    dish_name = input("Enter dish name: ")

    # Get the price of the dish
    cursor.execute("SELECT price FROM dishes WHERE dish_name=?", (dish_name,))
    result = cursor.fetchone()

    # If the dish exists
    if result is not None:
        price = result[0]
        total_price = price

        # Get the highest order ID
        cursor.execute("SELECT MAX(order_id) FROM orders")
        highest_id = cursor.fetchone()[0]

        # If there are no existing orders, set the order ID to 1
        if highest_id is None:
            new_id = 1
        else:
            new_id = highest_id + 1

        # Update the order table
        date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO orders (order_id, customer_name, dish_name, total_price, date) VALUES (?, ?, ?, ?, ?)",
                       (new_id, customer_name, dish_name, total_price, date))

        # Update the amount_on_hand of all ingredients used in the dish
        cursor.execute("SELECT ingredient_name FROM dish_ingredients WHERE dish_name=?", (dish_name,))
        ingredients = cursor.fetchall()

        for ingredient in ingredients:
            cursor.execute("UPDATE ingredients SET amount_on_hand = amount_on_hand - 1 WHERE ingredient_name=?",
                           (ingredient[0],))

        print(f"Order placed successfully. Total price: ${total_price:.2f}")

    # If the dish does not exist
    else:
        print("Dish not found. Please check the dish name and try again.")

def lookup_recent_orders(cursor):
    # lists 20 most recent orders
    cursor.execute("SELECT * FROM orders ORDER BY date DESC LIMIT 20")
    orders = cursor.fetchall()

    if not orders:
        print("No recent orders found.")
    else:
        print("\nRecent Orders:")
        for order in orders:
            print(f"Customer: {order[1]}, Dish: {order[2]}, Date: {order[4]}\n")


def update_prices(cursor):
    # Prompt for which item and the new price
    item_name = input("Enter the item name to update the price: ")
    new_price = float(input("Enter the new price: "))

    # Update the db
    cursor.execute("UPDATE dishes SET price = ? WHERE dish_name = ?", (new_price, item_name))
    print(f"Price for {item_name} updated successfully.")

def add_item(cursor):
    # Prompt for dish fields
    dish_name = input("Enter the new dish name: ")
    price = float(input("Enter the price of the dish: "))
    profit_margin = float(input("Enter the profit margin for the dish: "))

    # Check if the dish already exists
    cursor.execute("SELECT * FROM dishes WHERE dish_name=?", (dish_name,))
    existing_dish = cursor.fetchone()

    if existing_dish:
        print(f"'{dish_name}' already exists.")
        return

    # Insert new dish into dishes table
    cursor.execute("INSERT INTO dishes (dish_name, price, profit_margin) VALUES (?, ?, ?)",
                   (dish_name, price, profit_margin))

    # Prompt for ingredients and add them to the dish_ingredients table
    while True:
        ingredient_name = input("Enter ingredient name (or 'done' to finish): ")

        if ingredient_name.lower() == 'done':
            break

        # Check if the ingredient already exists
        cursor.execute("SELECT * FROM ingredients WHERE ingredient_name=?", (ingredient_name,))
        existing_ingredient = cursor.fetchone()

        if not existing_ingredient:
            # If the ingredient does not exist, add it with default values
            cursor.execute("INSERT INTO ingredients (ingredient_name, price_per_pound, supplier, amount_on_hand) "
                           "VALUES (?, NULL, 'Not Yet Added', 10)", (ingredient_name,))

        # Add the ingredient to the dish_ingredients table
        cursor.execute("INSERT INTO dish_ingredients (dish_name, ingredient_name) VALUES (?, ?)",
                       (dish_name, ingredient_name))

    # Confirmation
    print(f"{dish_name} added successfully.")

def remove_item(cursor):
    # Prompt for what dish
    dish_name = input("Enter the dish name to remove: ")

    # Remove from dishes table
    cursor.execute("DELETE FROM dishes WHERE dish_name=?", (dish_name,))

    # Remove from dish_ingredients table
    cursor.execute("DELETE FROM dish_ingredients WHERE dish_name=?", (dish_name,))

    # Confirmation
    print(f"Dish {dish_name} removed successfully.")

def sales_info(cursor):
    # Display options:
    print("Sales Information Options:")
    print("1: 5 Best Selling Items")
    print("2: Best Customers by $")
    print("3: Best Customers by Total Orders")
    print("4: Highest Profit Items")
    print("5: Most Popular Ingredients")

    choice = input("Enter your choice: ")

    if choice == '1':
        cursor.execute("SELECT dish_name, SUM(total_price) AS total_sales FROM orders GROUP BY dish_name ORDER BY total_sales DESC LIMIT 5")
        result = cursor.fetchall()
        print("\n5 Best Selling Items:")
        for item in result:
            print(f"{item[0]} - Total Sales: ${item[1]:.2f}")
            
    elif choice == '2':
        cursor.execute("SELECT customer_name, SUM(total_price) AS total_spent FROM orders GROUP BY customer_name ORDER BY total_spent DESC LIMIT 5")
        result = cursor.fetchall()
        print("\nBest Customers by $:")
        for customer in result:
            print(f"{customer[0]} - Total Spent: ${customer[1]:.2f}")
            
    elif choice == '3':
        cursor.execute("SELECT customer_name, COUNT(*) AS total_orders FROM orders GROUP BY customer_name ORDER BY total_orders DESC LIMIT 5")
        result = cursor.fetchall()
        print("\nBest Customers by Total Orders:")
        for customer in result:
            print(f"{customer[0]} - Total Orders: {customer[1]}")
            
    elif choice == '4':
        cursor.execute("SELECT dish_name, profit_margin FROM dishes ORDER BY profit_margin DESC LIMIT 5")
        result = cursor.fetchall()
        print("\nHighest Profit Items:")
        for item in result:
            print(f"{item[0]} - Profit Margin: {item[1]}")
            
    elif choice == '5':
        cursor.execute("SELECT ingredient_name, COUNT(dish_name) AS num_dishes FROM dish_ingredients GROUP BY ingredient_name ORDER BY num_dishes DESC LIMIT 5")
        result = cursor.fetchall()
        print("\nMost Popular Ingredients:")
        for ingredient in result:
            print(f"{ingredient[0]} - Used in {ingredient[1]} dishes")

def plot_sales(cursor):
    # Create and open a numpy graph that shows total sales per day of the week
    cursor.execute("SELECT strftime('%w', date) AS day_of_week, SUM(total_price) FROM orders GROUP BY day_of_week")
    result = cursor.fetchall()

    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    sales = [0] * 7

    for item in result:
        sales[int(item[0])] = item[1]

    plt.bar(days, sales, color='blue')
    plt.xlabel('Day of the Week')
    plt.ylabel('Total Sales')
    plt.title('Total Sales per Day of the Week')
    plt.show()

def plot_menu(cursor):
    # Create and open a numpy histogram that shows item popularity
    cursor.execute("SELECT dish_name, COUNT(*) FROM orders GROUP BY dish_name")
    result = cursor.fetchall()

    items = [item[0] for item in result]
    order_counts = [item[1] for item in result]

    plt.bar(items, order_counts, color='green')
    plt.xlabel('Dish Name')
    plt.ylabel('Number of Orders')
    plt.title('Popularity of Items in the Menu')
    plt.xticks(rotation=45, ha='right')
    plt.show()

def custom_query(cursor):
    # Display the db information for the user
    print("\nYou can use the following schema to build your own custom queries:")
    print("TABLE 'ingredients'('ingredient_name', 'price_per_pound', 'supplier', 'amount_on_hand')")
    print("TABLE 'dishes'('dish_name', 'price', 'profit_margin')")
    print("TABLE 'dish_ingredients'('dish_name', 'ingredient_name')")
    print("TABLE 'orders'('order_id', 'customer_name', 'dish_name', 'total_price', 'date')\n")

    # Prompt for query
    query = input("\nEnter your custom query: ")

    try:
        # Execute and print result
        cursor.execute(query)
        result = cursor.fetchall()

        if result:
            print("\nQuery Result:")
            for row in result:
                print(row)
        else:
            print("No results found for the query.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        print("Please try again")

def list_inventory(cursor):
    # Get all ingredients
    cursor.execute("SELECT * FROM ingredients")
    inventory = cursor.fetchall()

    # If none found (unlikely unless someone deleted everything which is technically possible)
    if not inventory:
        print("No ingredients found.")
    # Else
    else:
        # Print everything and the amounts
        print("\nInventory:")
        for item in inventory:
            print(f"Ingredient: {item[0]}, Amount on Hand: {item[3]}")


def list_suppliers(cursor):
    # Get all suppliers
    cursor.execute("SELECT DISTINCT supplier FROM ingredients")
    suppliers = cursor.fetchall()

    # If none (again, almost certainly wont happen)
    if not suppliers:
        print("No suppliers found.")
    # Else
    else:
        # Print the suppliers and all the things they supply
        print("\nSuppliers:")
        for supplier in suppliers:
            print(supplier[0])

            cursor.execute("SELECT ingredient_name FROM ingredients WHERE supplier=?", (supplier[0],))
            items = cursor.fetchall()

            for item in items:
                print(f"-- {item[0]}")

def low_ingredients(cursor):
    # Get all ingredients with amount_on_hand less than 10
    cursor.execute("SELECT ingredient_name, amount_on_hand FROM ingredients WHERE amount_on_hand < 10")
    low_items = cursor.fetchall()

    # If none
    if not low_items:
        print("No low ingredients found.")
    # Else
    else:
        # Print all found and current amounts
        print("\nLow Ingredients:")
        for item in low_items:
            print(f"Ingredient: {item[0]}, Amount on Hand: {item[1]}")

def order_ingredients(cursor):
    # Prompt for which ingredient
    ingredient_name = input("Enter the ingredient name to order: ")
    # Arbitrary order quantity
    AMOUNT = 10

    # Update
    cursor.execute("UPDATE ingredients SET amount_on_hand = amount_on_hand + ? WHERE ingredient_name = ?",
                   (AMOUNT, ingredient_name))

    cursor.execute("SELECT amount_on_hand FROM ingredients WHERE ingredient_name = ?", (ingredient_name,))
    new_quantity = cursor.fetchone()[0]

    # Confirmation
    print(f"Order placed successfully. New quantity for {ingredient_name}: {new_quantity}")

def menu_options(cursor):
    while True:
        print("\nMenu Options:")
        print("1: Update Prices")
        print("2: Add Item")
        print("3: Remove Item")
        print("0: Back\n")

        choice = input("Enter your choice: ")

        if choice == '1':
            update_prices(cursor)
        elif choice == '2':
            add_item(cursor)
        elif choice == '3':
            remove_item(cursor)
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def inventory_options(cursor):
        while True:
            print("\nInventory Options:")
            print("1: List Inventory")
            print("2: List Suppliers")
            print("3: List Low Ingredients")
            print("4: Order Ingredients")
            print("0: Back\n")

            choice = input("Enter your choice: ")

            if choice == '1':
                list_inventory(cursor)
            elif choice == '2':
                list_suppliers(cursor)
            elif choice == '3':
                low_ingredients(cursor)
            elif choice == '4':
                order_ingredients(cursor)
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please try again.")

def data_options(cursor):
    while True:
        print("\nData Options:")
        print("1: Check Sales Information")
        print("2: Plot Sales Data")
        print("3: Plot Menu Data")
        print("4: Submit Custom Query")
        print("0: Back\n")

        choice = input("Enter your choice: ")

        if choice == '1':
            sales_info(cursor)
        elif choice == '2':
            plot_sales(cursor)
        elif choice == '3':
            plot_menu(cursor)
        elif choice == '4':
            custom_query(cursor)
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    # Connect to db
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()

    while True:
        print("\nMain Menu:")
        print("1: Print Menu")
        print("2: Place Order")
        print("3: Look Up Recent Orders")
        print("4: Menu Options")
        print("5: Inventory Options")
        print("6: Data Options")
        print("0: Exit\n")

        choice = input("Enter your choice: ")

        if choice == '1':
            print_menu(cursor)
        elif choice == '2':
            add_order(cursor)
        elif choice == '3':
            lookup_recent_orders(cursor)
        elif choice == '4':
            menu_options(cursor)
        elif choice == '5':
            inventory_options(cursor)
        elif choice == '6':
            data_options(cursor)
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
