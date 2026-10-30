import customtkinter as ctk
import nmap
import requests
import threading
from reportlab.pdfgen import canvas
import os

# GUI Theme Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VulnDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AutoRecon Vulnerability Dashboard")
        self.geometry("700x600")

        # UI Elements
        self.label = ctk.CTkLabel(self, text="Target IP or Domain:", font=("Arial", 16, "bold"))
        self.label.pack(pady=10)

        self.target_entry = ctk.CTkEntry(self, width=400, placeholder_text="e.g., 192.168.1.1 or scanme.nmap.org")
        self.target_entry.pack(pady=10)

        self.scan_btn = ctk.CTkButton(self, text="Start Scan", command=self.start_scan_thread)
        self.scan_btn.pack(pady=10)

        self.result_textbox = ctk.CTkTextbox(self, width=600, height=350, font=("Consolas", 12))
        self.result_textbox.pack(pady=20)

        self.pdf_btn = ctk.CTkButton(self, text="Download PDF Report", command=self.generate_pdf, state="disabled")
        self.pdf_btn.pack(pady=10)

        self.scan_results = ""

    def start_scan_thread(self):
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("end", "Initializing Scan... Please wait.\n")
        self.scan_btn.configure(state="disabled")
        self.pdf_btn.configure(state="disabled")
        
        # Threading prevents the GUI from freezing during the scan
        threading.Thread(target=self.run_scan).start()

    def run_scan(self):
        target = self.target_entry.get().strip()
        if not target:
            self.update_result("Error: Please enter a target.")
            self.scan_btn.configure(state="normal")
            return

        nm = nmap.PortScanner(nmap_search_path=[r"C:\Program Files (x86)\Nmap\nmap.exe", r"C:\Program Files\Nmap\nmap.exe", "nmap"])
        results = f"--- SCAN REPORT FOR {target} ---\n\n"
        
        # 1. Nmap Port Scan (Basic fast scan)
        try:
            self.update_result("[+] Running Port Scan...\n")
            nm.scan(target, arguments='-F') # Fast scan
            for host in nm.all_hosts():
                results += f"Host: {host} ({nm[host].hostname()})\n"
                results += f"State: {nm[host].state()}\n"
                for proto in nm[host].all_protocols():
                    ports = nm[host][proto].keys()
                    for port in ports:
                        state = nm[host][proto][port]['state']
                        results += f"Port: {port}\tState: {state}\n"
        except Exception as e:
            results += f"Nmap scan failed: {str(e)}\n"

        results += "\n"

        # 2. HTTP Security Headers Check
        try:
            self.update_result("[+] Checking HTTP Security Headers...\n")
            url = target if target.startswith("http") else f"http://{target}"
            response = requests.get(url, timeout=5)
            headers = response.headers
            
            results += "--- SECURITY HEADERS ---\n"
            missing_headers = []
            security_headers = ['X-Frame-Options', 'X-XSS-Protection', 'Content-Security-Policy', 'Strict-Transport-Security']
            
            for sh in security_headers:
                if sh not in headers:
                    missing_headers.append(sh)
            
            if missing_headers:
                results += f"Missing Headers (Vulnerabilities found):\n"
                for mh in missing_headers:
                    results += f"[-] {mh} is missing!\n"
            else:
                results += "All basic security headers are present.\n"
                
        except Exception as e:
            results += f"HTTP check skipped or failed.\n"

        # Finalize
        self.scan_results = results
        self.update_result(f"\nScan Completed!\n\n{results}")
        self.scan_btn.configure(state="normal")
        self.pdf_btn.configure(state="normal")

    def update_result(self, text):
        # Insert text at the end
        self.result_textbox.insert("end", text)
        self.result_textbox.see("end")

    def generate_pdf(self):
        filename = "Scan_Report.pdf"
        c = canvas.Canvas(filename)
        c.setFont("Helvetica", 10)
        
        y_position = 800
        for line in self.scan_results.split('\n'):
            c.drawString(50, y_position, line)
            y_position -= 15
            if y_position < 50:
                c.showPage()
                y_position = 800
        
        c.save()
        self.update_result(f"\n[+] PDF Saved successfully as {filename}\n")

if __name__ == "__main__":
    app = VulnDashboard()
    app.mainloop()