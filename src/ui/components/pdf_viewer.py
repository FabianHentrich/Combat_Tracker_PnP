import tkinter as tk
from tkinter import ttk, messagebox
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
from PIL import Image, ImageTk
import os
import webbrowser
from typing import Optional, Dict
from src.utils.logger import setup_logging

logger = setup_logging()

class PDFViewer(ttk.Frame):
    """
    A unified PDF Viewer component using PyMuPDF (fitz).
    Supports navigation (next/prev), zooming, resizing, ToC, and search.
    """
    def __init__(self, parent, colors: Dict[str, str], pdf_path: Optional[str] = None):
        super().__init__(parent)
        self.colors = colors
        self.doc: Optional[fitz.Document] = None

        # State
        self.current_page_num = 0
        self.total_pages = 0
        self.zoom_level = 1.0

        # Continuous scrolling state
        self.page_images = {}      # {page_num: ImageTk.PhotoImage}
        self.page_layouts = []     # List of (y_offset, height, width) for each page
        self.rendered_pages = set() # Set of currently rendered page numbers
        self.link_rects = {}       # {page_num: [canvas_item_ids]}
        self.total_height = 0
        self.max_width = 0

        self.search_results = []
        self.current_search_index = -1

        # UI Layout
        self._setup_ui()

        if pdf_path:
            self.load_file(pdf_path)

    def _setup_ui(self):
        # Paned Window for Sidebar (ToC) and Main Content
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # --- Sidebar (ToC) ---
        self.sidebar = ttk.Frame(self.paned, style="Card.TFrame")
        self.paned.add(self.sidebar, weight=1)

        ttk.Label(self.sidebar, text="Inhalt", font=("Segoe UI", 10, "bold")).pack(pady=5)

        self.toc_tree = ttk.Treeview(self.sidebar, selectmode="browse", show="tree")
        self.toc_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        scrollbar_toc = ttk.Scrollbar(self.sidebar, orient="vertical", command=self.toc_tree.yview)
        self.toc_tree.configure(yscrollcommand=scrollbar_toc.set)
        scrollbar_toc.pack(side=tk.RIGHT, fill=tk.Y)
        self.toc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.toc_tree.bind("<<TreeviewSelect>>", self._on_toc_select)

        # --- Main Content Area ---
        self.main_area = ttk.Frame(self.paned)
        self.paned.add(self.main_area, weight=4)

        # Toolbar
        self.toolbar = ttk.Frame(self.main_area, style="Card.TFrame")
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Navigation
        self.btn_prev = ttk.Button(self.toolbar, text="<", command=self.prev_page, width=3)
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.page_var = tk.StringVar()
        self.entry_page = ttk.Entry(self.toolbar, textvariable=self.page_var, width=5, justify="center")
        self.entry_page.pack(side=tk.LEFT, padx=5)
        self.entry_page.bind("<Return>", self._on_page_entry)

        self.lbl_total_pages = ttk.Label(self.toolbar, text="/ 0", font=("Segoe UI", 9))
        self.lbl_total_pages.pack(side=tk.LEFT, padx=2)

        self.btn_next = ttk.Button(self.toolbar, text=">", command=self.next_page, width=3)
        self.btn_next.pack(side=tk.LEFT, padx=2)

        # Zoom
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        self.btn_zoom_out = ttk.Button(self.toolbar, text="-", command=self.zoom_out, width=3)
        self.btn_zoom_out.pack(side=tk.LEFT, padx=2)

        self.lbl_zoom = ttk.Label(self.toolbar, text="100%", font=("Segoe UI", 9))
        self.lbl_zoom.pack(side=tk.LEFT, padx=5)

        self.btn_zoom_in = ttk.Button(self.toolbar, text="+", command=self.zoom_in, width=3)
        self.btn_zoom_in.pack(side=tk.LEFT, padx=2)

        # Search
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        self.search_var = tk.StringVar()
        self.entry_search = ttk.Entry(self.toolbar, textvariable=self.search_var, width=15)
        self.entry_search.pack(side=tk.LEFT, padx=5)
        self.entry_search.bind("<Return>", lambda e: self.search_next())

        self.btn_search_prev = ttk.Button(self.toolbar, text="▲", command=self.search_prev, width=3)
        self.btn_search_prev.pack(side=tk.LEFT, padx=1)
        self.btn_search_next = ttk.Button(self.toolbar, text="▼", command=self.search_next, width=3)
        self.btn_search_next.pack(side=tk.LEFT, padx=1)

        self.lbl_search_status = ttk.Label(self.toolbar, text="", font=("Segoe UI", 8))
        self.lbl_search_status.pack(side=tk.LEFT, padx=5)

        # Content Area (Canvas)
        self.canvas_frame = ttk.Frame(self.main_area)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=self.colors.get("bg", "#ffffff"),
            highlightthickness=0,
            yscrollcommand=self._on_canvas_y_scroll,
            xscrollcommand=self.h_scroll.set
        )

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Configure>", self._on_resize)
        # Bind click for links
        self.canvas.bind("<Button-1>", self._check_link_click)
        self.canvas.bind("<Motion>", self._check_link_hover)

    def _on_canvas_y_scroll(self, first, last):
        self.v_scroll.set(first, last)
        self._check_visible_pages()
        self._update_current_page_indicator()

    def load_file(self, path: str):
        logger.info(f"Attempting to load PDF: {path}")
        if not fitz:
            logger.error("PyMuPDF (fitz) not installed.")
            self.lbl_total_pages.config(text="Error: pymupdf missing")
            return

        if not os.path.exists(path):
            logger.warning(f"PDF File not found: {path}")
            self.lbl_total_pages.config(text="File not found")
            return

        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(path)
            self.total_pages = len(self.doc)
            self.current_page_num = 0
            self.zoom_level = 1.0
            logger.info(f"PDF loaded successfully. Pages: {self.total_pages}")

            # Reset logic
            self.canvas.delete("all")
            self.page_images.clear()
            self.rendered_pages.clear()

            try:
                self._load_toc()
            except Exception as e:
                logger.error(f"Error loading TOC: {e}")

            self._calculate_page_geometry()
            self._update_view() # Initial render
        except Exception as e:
            logger.error(f"Critical error loading PDF: {e}")
            messagebox.showerror("PDF Error", f"Could not open PDF:\n{str(e)}")

    def _calculate_page_geometry(self):
        """Calculates size and position for all pages based on zoom level."""
        if not self.doc: return

        self.page_layouts = []
        y = 0
        max_w = 0
        margin = 10 # px between pages

        for i in range(self.total_pages):
            page = self.doc[i]
            # Use cropbox or rect? usually rect is fine.
            rect = page.rect
            w = rect.width * self.zoom_level
            h = rect.height * self.zoom_level

            self.page_layouts.append((y, h, w))

            y += h + margin
            if w > max_w: max_w = w

        self.total_height = y
        self.max_width = max_w

        self.canvas.config(scrollregion=(0, 0, max_w, self.total_height))

    def _check_visible_pages(self):
        """Determines which pages are currently visible and renders them."""
        if not self.page_layouts: return

        # Get visible y-range in pixels
        top_frac, bot_frac = self.canvas.yview()
        top_y = top_frac * self.total_height
        bot_y = bot_frac * self.total_height

        # Add buffer (e.g. 1000px up/down)
        top_y -= 1000
        bot_y += 1000

        visible_indices = set()

        for i, (py, ph, pw) in enumerate(self.page_layouts):
            # Check overlap
            if (py + ph > top_y) and (py < bot_y):
                visible_indices.add(i)

        # Render new pages
        for i in visible_indices:
            if i not in self.rendered_pages:
                self._render_page_continuous(i)

        # Unload hidden pages
        to_remove = set(self.rendered_pages) - visible_indices
        for i in to_remove:
            self._unload_page(i)

    def _render_page_continuous(self, page_num):
        if not self.doc: return

        try:
            page = self.doc.load_page(page_num)
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)
            img_data = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            tk_img = ImageTk.PhotoImage(img_data)

            # Store ref
            self.page_images[page_num] = tk_img
            self.rendered_pages.add(page_num)

            # Position
            y, h, w = self.page_layouts[page_num]

            # Center horizontally?
            x = 0 # Align left for now, or (self.max_width - w) / 2

            # Draw image
            # Tag with "page_X" to easily manipulate later
            self.canvas.create_image(x, y, image=tk_img, anchor="nw", tags=(f"page_{page_num}", "page_content"))

            # Links
            self._draw_links(page, page_num, mat, x, y)

            # Search highlights if any match on this page
            self._draw_search_highlights(page, mat, x, y)

        except Exception as e:
            logger.error(f"Error rendering page {page_num}: {e}")

    def _draw_links(self, page, page_num, matrix, offset_x, offset_y):
        links = page.get_links()
        if not links: return

        if page_num not in self.link_rects:
            self.link_rects[page_num] = []

        for link in links:
            # link['from'] is rect
            rect = link['from']
            # Transform rect by matrix
            # fitz.Rect * fitz.Matrix -> fitz.Rect
            t_rect = rect * matrix

            x0 = offset_x + t_rect.x0
            y0 = offset_y + t_rect.y0
            x1 = offset_x + t_rect.x1
            y1 = offset_y + t_rect.y1

            # Create transparent rectangle
            # stipple="" means transparent, but it handles events
            # Need fill to catch mouse, but alpha?
            # Tkinter canvas polygons/rects are clickable if they have fill (even if transparent? No, usually distinct).
            # We can use stipple='gray12' with a very light color or similar trick, but Tkinter "transparent" fill is tricky.
            # Workaround: Use creating a rect with fill="" (empty) only catches clicks on border?
            # Using fill with alpha is not supported natively.
            # Best way: bind click on canvas and check coordinates? Or use window items?
            # Or assume users won't mind a faint highlight on links.

            # Actually, create_rectangle(..., fill="", outline="") is invisible but does NOT catch events strictly inside?
            # Let's try fill not None. But we want invisible.
            # "Any non-empty string for fill makes it filled"

            # Improved approach: Just create the rect with a specific tag and bind to tag.
            # But the rect must be 'filled' to receive clicks inside.
            # We can create a rect with fill but make it almost invisible, or just use the coordinate click approach if this fails.
            # But specific tag bindings are cleaner.

            # Let's try empty fill but non-empty outline? No.
            # Let's use a very transparent look? Not possible easily.

            # Wait, `canvas.find_overlapping` works even on invisible items?
            # If fill is empty string, it is transparent.

            # Let's create an item with tag f"link_{link_id}".
            # We will store the link data.

            link_tag = f"link_{page_num}_{id(link)}"

            # We will use stipple to make it faint blue if desired, or invisible.
            # Let's try the invisible trick: fill="" and outline=""
            # And see if bind works. (Usually it doesn't for the interior).

            # Alternative: Keep a list of link rects and check on canvas click.
            # This is reliable.
            self.link_rects[page_num].append((x0, y0, x1, y1, link))

    def _check_link_click(self, event):
        # Convert window/event coords to canvas coords
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # Check rendered pages to find which one we are on
        # Optimization: Find page by y
        for vid in self.rendered_pages:
            py, ph, pw = self.page_layouts[vid]
            if py <= cy <= py + ph:
                # We are on this page
                if vid in self.link_rects:
                    for (x0, y0, x1, y1, link) in self.link_rects[vid]:
                        if x0 <= cx <= x1 and y0 <= cy <= y1:
                            self._handle_link_action(link)
                            return
                break

    def _handle_link_action(self, link):
        if "uri" in link and link["uri"]:
            webbrowser.open(link["uri"])
        elif "page" in link:
            # link['page'] is 0-based index
            target = link["page"]
            self.jump_to_page(target)
        elif "kind" in link and link["kind"] == fitz.LINK_GOTO:
             # handle GOTO if stored differently
             # usually 'page' key is present
             pass

    def _unload_page(self, page_num):
        if page_num in self.page_images:
            del self.page_images[page_num]

        self.canvas.delete(f"page_{page_num}")
        if page_num in self.rendered_pages:
            self.rendered_pages.remove(page_num)

        # We don't need to delete link rects data, it's just coords, low memory.

    def _update_current_page_indicator(self):
        # Find which page is in center of view
        top, bot = self.canvas.yview()
        mid_y = (top + bot) / 2 * self.total_height

        # Binary search or linear? Linear is fine for now on sorted layouts
        found_page = 0
        for i, (py, ph, pw) in enumerate(self.page_layouts):
            if py <= mid_y <= py + ph:
                found_page = i
                break
            if py > mid_y: # passed it (if mid_y is before first page?)
                break

        if found_page != self.current_page_num:
            self.current_page_num = found_page
            self.page_var.set(str(self.current_page_num + 1))
            self.lbl_total_pages.config(text=f"/ {self.total_pages}")

            # Also update nav buttons state
            self.btn_prev.state(["!disabled"] if self.current_page_num > 0 else ["disabled"])
            self.btn_next.state(["!disabled"] if self.current_page_num < self.total_pages - 1 else ["disabled"])

    # ... The rest of methods ...

    def _load_toc(self):

        self.toc_tree.delete(*self.toc_tree.get_children())
        if not self.doc:
            return

        try:
            toc = self.doc.get_toc()
            logger.debug(f"TOC loaded with {len(toc)} entries.")
        except Exception as e:
            logger.warning(f"Failed to retrieve TOC from document: {e}")
            return

        stack = []

        for item in toc:
            if len(item) < 3: continue

            lvl = item[0]
            title = item[1]
            page = item[2]

            parent_id = ""
            while stack and stack[-1][0] >= lvl:
                stack.pop()

            if stack:
                parent_id = stack[-1][1]

            page_num = page - 1 if page > 0 else 0
            node_id = self.toc_tree.insert(parent_id, "end", text=title, values=(page_num,))
            stack.append((lvl, node_id))

    def _on_toc_select(self, event):
        selection = self.toc_tree.selection()
        if not selection:
            return
        item = self.toc_tree.item(selection[0])
        values = item.get("values")
        if values:
            page = int(values[0])
            self.jump_to_page(page)

    def jump_to_page(self, page_num: int):
        if not self.doc: return

        # Clamp
        page_num = max(0, min(page_num, self.total_pages - 1))

        # Get y offset
        if page_num < len(self.page_layouts):
            y, h, w = self.page_layouts[page_num]
            # Scroll to y
            if self.total_height > 0:
                fraction = y / self.total_height
                self.canvas.yview_moveto(fraction)

                # Force update of visible pages manually as yview_moveto might not trigger scroll event immediately
                self.update_idletasks()
                self._check_visible_pages()
                self._update_current_page_indicator()

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        self.canvas.config(bg=colors.get("bg", "#ffffff"))
        # Refresh rendered pages if needed or just let next render handle it?
        # Ideally we should reload current view to apply bg change if transparency is involved
        self._update_view()

    def _on_page_entry(self, event):
        try:
            val = int(self.page_var.get())
            self.jump_to_page(val - 1)
        except ValueError:
            pass

    def _update_view(self):
        # Triggered on zoom or load
        self.canvas.delete("all")
        self.page_images.clear()
        self.rendered_pages.clear()
        self.link_rects.clear()

        self._calculate_page_geometry()

        # Restore scroll pos? For now reset to top or current page
        # If zooming, try to keep current page
        if self.current_page_num < len(self.page_layouts):
             self.jump_to_page(self.current_page_num)

        self.lbl_zoom.config(text=f"{int(self.zoom_level * 100)}%")

    def _draw_search_highlights(self, page, matrix, offset_x, offset_y):
        # Only if we have search results
        if not self.search_results: return

        # Need to fix search result indexing if we use continuous search
        # search_results contains (p_idx, rect)

        # Filter for this page
        # Optimize if list is sorted by page? Yes usually.

        for i, (p_num, rect) in enumerate(self.search_results):
            if p_num == self.doc.load_page(p_num).number: # Check page number match?
                # Actually self.doc[i] object page number...
                # p_idx stored in search_results IS the page number
                pass

            if p_num == page.number:
                t_rect = rect * matrix
                x0 = offset_x + t_rect.x0
                y0 = offset_y + t_rect.y0
                x1 = offset_x + t_rect.x1
                y1 = offset_y + t_rect.y1

                color = "#FFFF00"
                if i == self.current_search_index:
                    color = "#FF9900"

                self.canvas.create_rectangle(
                    x0, y0, x1, y1,
                    outline=color, width=2, stipple="gray50", fill=color,
                    tags=f"highlight_{p_num}"
                )

    def next_page(self):
        self.jump_to_page(self.current_page_num + 1)

    def prev_page(self):
        self.jump_to_page(self.current_page_num - 1)

    def zoom_in(self):
        if self.zoom_level < 3.0:
            self.zoom_level += 0.25
            self._update_view()

    def zoom_out(self):
        if self.zoom_level > 0.25:
            self.zoom_level -= 0.25
            self._update_view()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # Re-added binding for links
    def _bind_canvas_events(self):
        self.canvas.bind("<Button-1>", self._check_link_click)

    def _on_resize(self, event):
        # Optional: Auto-fit to width could be implemented here
        pass

    def search_next(self):
        self._search(1)

    def search_prev(self):
        self._search(-1)

    def _search(self, direction):
        if not self.doc:
            return

        query = self.search_var.get()
        if not query:
            return

        # If it's a new query, search entire doc
        if not hasattr(self, '_last_query') or self._last_query != query:
             logger.info(f"Starting new search for: '{query}'")
             self._perform_full_search(query)

        if not self.search_results:
            self.lbl_search_status.config(text="0/0")
            logger.info("No matches found.")
            return

        # Move index
        self.current_search_index = (self.current_search_index + direction) % len(self.search_results)

        # Update status
        self.lbl_search_status.config(text=f"{self.current_search_index + 1}/{len(self.search_results)}")

        # Jump to page
        page_num, _ = self.search_results[self.current_search_index]
        self.jump_to_page(page_num)
        # We need to force update/redraw to ensure highlights are drawn if page was already rendered?
        # _render_page_continuous handles highlights. If page is already rendered, we might need to refresh highligts.
        # But for now, scrolling to it triggers checks.

    def search(self, text: str) -> int:
        """Public entry point for programmatic search. Returns match count."""
        if not self.doc or not text:
            return 0
        self._perform_full_search(text)
        if self.search_results:
            self.current_search_index = 0
            self._update_view()
            page_num, _ = self.search_results[0]
            self.jump_to_page(page_num)
        return len(self.search_results)

    def _perform_full_search(self, text):
        logger.debug(f"Scanning document for '{text}'...")
        self.search_results = []
        self._last_query = text
        self.current_search_index = -1

        for p_idx in range(self.total_pages):
            page = self.doc[p_idx]
            rects = page.search_for(text)
            for r in rects:
                self.search_results.append((p_idx, r))

        logger.info(f"Search found {len(self.search_results)} occurrences.")

        # Force re-render to update highlights
        self._update_view()

        if self.search_results:
             self.current_search_index = -1

    def _check_link_hover(self, event):
        """Changes cursor if hovering over a link."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        is_hovering = False
        # Optimization: Find page by y
        for vid in self.rendered_pages:
            py, ph, pw = self.page_layouts[vid]
            if py <= cy <= py + ph:
                if vid in self.link_rects:
                    for (x0, y0, x1, y1, link) in self.link_rects[vid]:
                        if x0 <= cx <= x1 and y0 <= cy <= y1:
                            is_hovering = True
                            break
                break

        self.canvas.config(cursor="hand2" if is_hovering else "")



