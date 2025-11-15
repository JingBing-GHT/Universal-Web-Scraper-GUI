import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import pandas as pd
import threading
import os
from urllib.parse import urljoin, urlparse
import time


class WebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("全能网页爬虫工具 v1.0")
        self.root.geometry("800x600")

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # URL输入区域
        url_frame = ttk.LabelFrame(main_frame, text="爬取目标", padding="5")
        url_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(url_frame, text="目标URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

        ttk.Label(url_frame, text="User-Agent:").grid(row=1, column=0, sticky=tk.W)
        self.ua_entry = ttk.Entry(url_frame, width=60)
        self.ua_entry.insert(0, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.ua_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        # 批量URL输入
        ttk.Label(url_frame, text="批量URL(每行一个):").grid(row=2, column=0, sticky=tk.W)
        self.batch_text = scrolledtext.ScrolledText(url_frame, width=60, height=4)
        self.batch_text.grid(row=2, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        # 控制按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.start_btn = ttk.Button(btn_frame, text="开始爬取", command=self.start_scraping)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="清空结果", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="爬取结果", padding="5")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.result_text = scrolledtext.ScrolledText(result_frame, width=80, height=20)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        url_frame.columnconfigure(1, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        self.scraped_data = []

    def start_scraping(self):
        urls = []
        single_url = self.url_entry.get().strip()
        batch_urls = self.batch_text.get("1.0", tk.END).strip().split('\n')

        if single_url:
            urls.append(single_url)
        urls.extend([url for url in batch_urls if url])

        if not urls:
            messagebox.showwarning("警告", "请输入至少一个URL")
            return

        self.start_btn.config(state='disabled')
        self.progress.start()
        self.result_text.delete('1.0', tk.END)
        self.scraped_data = []

        # 在新线程中执行爬取
        thread = threading.Thread(target=self.scrape_urls, args=(urls,))
        thread.daemon = True
        thread.start()

    def scrape_urls(self, urls):
        headers = {
            'User-Agent': self.ua_entry.get() or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for i, url in enumerate(urls):
            try:
                self.result_text.insert(tk.END, f"正在爬取: {url}\n")
                self.result_text.see(tk.END)
                self.root.update()

                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                # 提取各种信息
                title = soup.title.string if soup.title else "无标题"
                # 简单的正文提取（可根据需要增强）
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs[:3]])[:200] + "..."

                # 提取图片
                images = [img['src'] for img in soup.find_all('img') if img.get('src')][:5]
                # 确保图片URL完整
                images = [urljoin(url, img) for img in images]

                # 提取链接
                links = [a['href'] for a in soup.find_all('a') if a.get('href')][:10]
                links = [urljoin(url, link) for link in links]

                data = {
                    'url': url,
                    'title': title,
                    'content_preview': content,
                    'images': ', '.join(images),
                    'links': ', '.join(links),
                    'status': '成功'
                }

                self.scraped_data.append(data)
                self.result_text.insert(tk.END, f"✓ 成功: {title}\n")

            except Exception as e:
                error_data = {
                    'url': url,
                    'title': '爬取失败',
                    'content_preview': str(e),
                    'images': '',
                    'links': '',
                    'status': f'失败: {str(e)}'
                }
                self.scraped_data.append(error_data)
                self.result_text.insert(tk.END, f"✗ 失败: {url} - {str(e)}\n")

            self.result_text.see(tk.END)
            self.root.update()
            time.sleep(1)  # 礼貌性延迟

        self.progress.stop()
        self.start_btn.config(state='normal')
        self.result_text.insert(tk.END,
                                f"\n爬取完成！共处理 {len(urls)} 个URL，成功 {len([d for d in self.scraped_data if d['status'] == '成功'])} 个\n")

    def clear_results(self):
        self.result_text.delete('1.0', tk.END)
        self.scraped_data = []

    def export_data(self):
        if not self.scraped_data:
            messagebox.showwarning("警告", "没有数据可导出")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                df = pd.DataFrame(self.scraped_data)
                if filename.endswith('.xlsx'):
                    df.to_excel(filename, index=False)
                else:
                    df.to_csv(filename, index=False, encoding='utf-8-sig')

                messagebox.showinfo("成功", f"数据已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")


def main():
    root = tk.Tk()
    app = WebScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
