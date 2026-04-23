import re
import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
import csv
import threading
import customtkinter
from bs4 import BeautifulSoup
from customtkinter import filedialog
from playwright.sync_api import sync_playwright


def track_price():
    global urls
    results_txt_box.configure(state='normal')
    track_product_price_btn.configure(state="disabled")
    check_price_btn.configure(state="disabled")
    all_products_data = []

    # Scraping Data
    def parse_single_item(html_content, url):
        # Soup Object
        soup = BeautifulSoup(html_content, "html.parser")
        # Product Name/Details
        product_name_details = soup.find("span", {"id": "productTitle"})
        product_price = soup.find("span", class_="a-price-whole")

        product_price_text = product_price.text if product_price else "Out of Stock/No Price"
        product_name_details_text = product_name_details.get_text(
            strip=True) if product_name_details else "Title Not Found (Dead Link)"

        all_products_data.append(
            {"URL": url, "Product Name": product_name_details_text, "Product Price": product_price_text})
        results_txt_box.insert("end", f"🛍️ ₹{product_price_text} | {product_name_details_text}\n\n")
        results_txt_box.see("end")

    def parse_search_results(html_content, url):
        # Soup Object
        soup = BeautifulSoup(html_content, "html.parser")
        # All products
        all_products = soup.find_all("div", {"data-component-type": "s-search-result"})

        for product in all_products:
            product_name_details = product.find("h2")
            product_price = product.find("span", class_="a-price-whole")

            product_name_details_text = product_name_details.get_text(strip=True) if product_name_details else (
                "Title Not Found (Dead "
                "Link)⚠️")
            product_price_text = product_price.text if product_price else "Out of Stock/No Price🛒❌"

            all_products_data.append(
                {"URL": url, "Product Name": product_name_details_text, "Product Price": product_price_text})
            results_txt_box.insert("end", f"🔍 ₹{product_price_text} | {product_name_details_text}\n")
            results_txt_box.see("end")

        results_txt_box.insert("end", "\n")

    def route_and_parse(current_url, html_content):
        # Changing the scraping Method according to the url/page
        if "/dp/" in current_url or "/gp/" in current_url:
            parse_single_item(html_content, current_url)
        elif "/s?" in current_url or "/search" in current_url:
            parse_search_results(html_content, current_url)

    # Extracting url using Regex
    raw_text = text_box_url.get("1.0", "end-1c")

    # This splits the giant string exactly at every 'http'
    split_urls = re.split(r'(?=https?://)', raw_text)

    # Clean up spaces and remove any empty strings
    urls = [u.strip() for u in split_urls if u.strip().startswith("http")]
    results_txt_box.delete("1.0", "end")
    results_txt_box.insert("end", "⏳ Scraping...\n\n")
    with sync_playwright() as p:
        # Fetching Amazon HTML
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/122.0.0.0 Safari/537.36'
        )
        for i, url in enumerate(urls, start=1):
            clean_url = url.strip()
            try:
                page = context.new_page()
                page.goto(clean_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)  # 5s human delay
                html_content = page.content()
                page.close()
                # print(f"Successfully Fetched url {i}")
                route_and_parse(clean_url, html_content)
            except Exception as e:
                results_txt_box.insert("end", f"Failed to fetch {url}:{e}")

        browser.close()
    results_txt_box.insert("end", "\n💾 Choose where to save your CSV...\n")
    save_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        title="Save Scraped Data"
    )
    if save_path:
        with open(save_path, "w", encoding="utf-8", newline="") as new_csv_file:
            field_names = ["URL", "Product Name", "Product Price"]
            writer = csv.DictWriter(new_csv_file, fieldnames=field_names)
            writer.writeheader()
            for product in all_products_data:
                writer.writerow(product)
            # results_txt_box.insert("end","Successfully Saved!!")
    else:
        results_txt_box.insert("end", "⚠️ Save cancelled by user.\n")

    track_product_price_btn.configure(state="normal")
    check_price_btn.configure(state="normal")
    results_txt_box.configure(state='disabled')

def check_price():
    results_txt_box.configure(state='normal')
    track_product_price_btn.configure(state="disabled")
    check_price_btn.configure(state="disabled")
    all_products_data = []

    file_path = filedialog.askopenfilename(title="Select a CSV file to track ", filetypes=[("CSV Files", "*.csv")])
    if not file_path:# TURN BUTTONS BACK ON IF CANCELLED
        track_product_price_btn.configure(state="normal")
        check_price_btn.configure(state="normal")
        results_txt_box.configure(state='disabled')
        return

    extracted_urls = []
    old_prices = {}

    try:
        with open(file_path, "r", encoding="utf-8") as r:
            reader = csv.DictReader(r)
            for row in reader:
                url = row.get("URL")
                price = row.get("Product Price")
                name = row.get("Product Name")
                if url and url not in extracted_urls:
                    extracted_urls.append(url)
                if name and price:
                    old_prices.update({f"{name}": price})
        # start_scraping_thread()
    except Exception as e:
        results_txt_box.configure(state='normal')
        results_txt_box.insert("end", f"Error reading file: {e}\n")
        results_txt_box.configure(state='disabled')

    def parse_single_item(html_content, url):
        # Soup Object
        soup = BeautifulSoup(html_content, "html.parser")
        # Product Name/Details
        product_name_details = soup.find("span", {"id": "productTitle"})
        product_price = soup.find("span", class_="a-price-whole")

        product_price_text = product_price.text if product_price else "Out of Stock/No Price"
        product_name_details_text = product_name_details.get_text(
            strip=True) if product_name_details else "Title Not Found (Dead Link)"

        # Comparing Old and New Prices
        status = ""
        if product_name_details_text in old_prices and product_price_text != "Out of Stock/No Price":
            try:
                old_val = float(old_prices[product_name_details_text].replace(',', '').strip())
                new_val = float(product_price_text.replace(',', '').strip())

                if old_val > new_val:
                    status = f" [📉 Dropped ₹{old_val - new_val}]"
                elif new_val > old_val:
                    status = f" [📈 Increased ₹{new_val - old_val}]"
                else:
                    status = " [⚖️ No Change]"
            except:
                pass

        all_products_data.append(
            {"URL": url, "Product Name": product_name_details_text, "Product Price": product_price_text})

        results_txt_box.insert("end", f"🛍️ ₹{product_price_text}{status} | {product_name_details_text}\n\n")
        results_txt_box.see("end")

    def parse_search_results(html_content, url):
        # Soup Object
        soup = BeautifulSoup(html_content, "html.parser")
        # All products
        all_products = soup.find_all("div", {"data-component-type": "s-search-result"})

        for product in all_products:
            product_name_details = product.find("h2")
            product_price = product.find("span", class_="a-price-whole")

            product_name_details_text = product_name_details.get_text(strip=True) if product_name_details else (
                "Title Not Found (Dead "
                "Link)⚠️")
            product_price_text = product_price.text if product_price else "Out of Stock/No Price🛒❌"

            # Comparing Old and New Prices
            status = ""
            # Comparing Old and New Prices
            status = ""
            if product_price_text != "Out of Stock/No Price🛒❌":
                if product_name_details_text in old_prices:
                    try:
                        old_val = float(old_prices[product_name_details_text].replace(',', '').strip())
                        new_val = float(product_price_text.replace(',', '').strip())

                        if new_val < old_val:
                            status = f" [📉 Dropped ₹{old_val - new_val}]"
                        elif new_val > old_val:
                            status = f" [📈 Increased ₹{new_val - old_val}]"
                        else:
                            status = " [⚖️ No Change]"
                    except:
                        pass
                else:
                    # This explains why the tag was missing!
                    status = " [✨ New Item/Title Changed]"

            all_products_data.append(
                {"URL": url, "Product Name": product_name_details_text, "Product Price": product_price_text})

            results_txt_box.insert("end", f"🔍 ₹{product_price_text}{status} | {product_name_details_text}\n\n")
            results_txt_box.see("end")

    def route_and_parse(current_url, html_content):
        # Changing the scraping Method according to the url/page
        if "/dp/" in current_url or "/gp/" in current_url:
            parse_single_item(html_content, current_url)
        elif "/s?" in current_url or "/search" in current_url:
            parse_search_results(html_content, current_url)
    def run_browser():
        results_txt_box.insert("end", "⏳ Checking live prices...\n\n")

        with sync_playwright() as p:
            # Fetching Amazon HTML
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/122.0.0.0 Safari/537.36'
            )
            for i, url in enumerate(extracted_urls, start=1):
                clean_url = url.strip()
                try:
                    page = context.new_page()
                    page.goto(clean_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(5000)  # 5s human delay
                    html_content = page.content()
                    page.close()
                    # print(f"Successfully Fetched url {i}")
                    route_and_parse(clean_url, html_content)
                except Exception as e:
                    results_txt_box.insert("end", f"Failed to fetch {url}:{e}")

            browser.close()
        track_product_price_btn.configure(state="normal")
        check_price_btn.configure(state="normal")
        results_txt_box.insert("end", "✅ Finished checking prices!\n")
        results_txt_box.configure(state='disabled')

    check_thread=threading.Thread(target=run_browser)
    check_thread.daemon = True
    check_thread.start()

def start_scraping_thread():
    scraper_thread = threading.Thread(target=track_price)
    scraper_thread.daemon = True
    scraper_thread.start()


# Main GUI
root = customtkinter.CTk()
root.geometry("500x610")
root.maxsize(500, 610)
root.minsize(500, 610)
root.title("Amazon-Price Tracker")

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

# Frames
f_label_txt_box = customtkinter.CTkFrame(root, fg_color="black")
f_btn_label_txt_box = customtkinter.CTkFrame(root, fg_color="black")

# Label-Header
l_head = customtkinter.CTkLabel(root, text="Amazon price-tracker", font=("Press Start 2P", 16), text_color="green")

# Text-Box/URL
l1 = customtkinter.CTkLabel(f_label_txt_box, text="Paste the URLs here -:", font=("Helvetica", 15, "bold"),
                            text_color="green")
text_box_url = customtkinter.CTkTextbox(f_label_txt_box, corner_radius=10,
                                        height=100,
                                        width=400,
                                        font=("Helvetica", 14, "italic"),
                                        fg_color="white",
                                        text_color="black")

# Buttons
track_product_price_btn = customtkinter.CTkButton(f_btn_label_txt_box, text="Track Price", font=("Helvetica", 12),
                                                  height=50, width=150, command=start_scraping_thread, corner_radius=14)
check_price_btn = customtkinter.CTkButton(f_btn_label_txt_box, text="Check Price", font=("Helvetica", 12), height=50,
                                          width=150, command=check_price, corner_radius=14)

# TextBox (For showing results)
l2 = customtkinter.CTkLabel(f_btn_label_txt_box, text="Results", font=("Helvetica", 15, "bold"), text_color="green")
results_txt_box = customtkinter.CTkTextbox(f_btn_label_txt_box, corner_radius=10,
                                           height=310,
                                           width=400,
                                           font=("Helvetica", 16, "bold"),
                                           fg_color="white",
                                           text_color="black",
                                           state="disabled")

# Packing all the things
l_head.pack(anchor="n")

f_label_txt_box.pack(pady=6, fill='x')
l1.pack(pady=5)
text_box_url.pack(anchor="s", pady=5)

f_btn_label_txt_box.pack(anchor='s', fill='x')
l2.pack(pady=7)
results_txt_box.pack(anchor="n")
track_product_price_btn.pack(side="left", expand=True, padx=10, pady=10)
check_price_btn.pack(side="left", expand=True, padx=10, pady=10)

root.mainloop()
