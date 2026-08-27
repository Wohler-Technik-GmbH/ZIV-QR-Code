import json
import os
from datetime import datetime

from nicegui import ui


# Data model
class QRCodeScanner:
    def __init__(self):
        self.scanned_code: str = ""
        self.status_message: str = "Ready"
        self.field_definitions: dict | None = None

    def load_field_definitions(self, filepath: str) -> None:
        """Loads field definitions from a JSON file."""
        try:
            with open(filepath, encoding="utf-8") as f:
                self.field_definitions = json.load(f)
                self.set_status("Field definitions loaded. Ready to scan.")
        except FileNotFoundError:
            self.set_status(f"Error: Definition file '{filepath}' not found. Raw data will be displayed.")
        except json.JSONDecodeError:
            self.set_status(f"Error: Definition file '{filepath}' contains invalid JSON.")

    def set_status(self, message: str) -> None:
        """Sets the current status message."""
        self.status_message = message

    def clear_scan(self) -> None:
        """Clears the scanned code."""
        self.scanned_code = ""
        self.set_status("Ready to scan.")

    def process_scan(self, scan_input: str) -> None:
        """Processes the scanned code."""
        self.scanned_code = scan_input
        if self.scanned_code.endswith("20G\n"):
            self.set_status("QR code scanned successfully.")

    def parse_qr_data(self, qr_data_list: list[str]) -> list[list[str | list]]:
        """Processes QR code data and returns it in structured form."""
        if not self.field_definitions:
            return [["Error", "No field definitions loaded"]]

        # Format validation
        if not self._validate_qr_format(qr_data_list):
            return [["Error", "Invalid QR code format"]]

        return self._process_qr_sections(qr_data_list)

    def _validate_qr_format(self, data_list: list[str]) -> bool:
        """Validates the format of QR code data."""
        if not data_list:
            return False
        format_checks = [(0, "1G"), (1, "3G"), (2, "4G"), (-1, "20G")]
        return all(i < len(data_list) and data_list[i].startswith(prefix) for i, prefix in format_checks)

    def _process_qr_sections(self, data_list: list[str]) -> list[list[str | list]]:
        """Processes individual sections of the QR code."""
        result = []
        current_section = {"title": None, "data": [], "number": None, "lookup": None}

        for element in data_list:
            if "G" not in element:
                continue

            field_id, value = element.split("G", 1)

            if field_id == "20":  # End of transmission
                if current_section["data"]:
                    result.append([current_section["title"], current_section["data"]])
                break

            elif field_id == "5":  # New section
                self._handle_section_change(current_section, result, value)

            elif field_id in ["1", "3", "4"]:  # General fields
                field_info = self.field_definitions["general_field"].get(field_id, {})
                description = field_info.get("description", "Unknown field")
                result.append([description, value])

            else:  # Section data
                self._process_section_field(current_section, field_id, value)

        return result

    def _handle_section_change(self, section: dict, result: list, value: str) -> None:
        """Handles the change to a new section (fully data-driven)."""
        if section["data"]:
            result.append([section["title"], section["data"]])

        section["number"] = value
        title_info = self.field_definitions["section_title"].get(value, {})
        section["title"] = title_info.get("description", "Unknown section")
        section["data"] = []

        section_data = self.field_definitions["section_data"]

        # Data-driven lookup strategy:
        # 1. Check if section has its own field definition
        # 2. If not, but defined in section_titles → use fallback "0"
        # 3. If not defined at all → use value itself (returns empty dict)
        if value in section_data:
            lookup_key = value
        elif value in self.field_definitions["section_title"]:
            lookup_key = "0"  # Fallback for sections without their own definition
        else:
            lookup_key = value  # Unknown section

        section["lookup"] = section_data.get(lookup_key, {})

    def _process_section_field(self, section: dict, field_id: str, value: str) -> None:
        """Processes a single field within a section."""
        field_info = section["lookup"].get(field_id, {})
        description = field_info.get("description", f"Unknown field {field_id}")

        formatted_value = self._format_field_value(value, field_info)
        section["data"].append([description, formatted_value])

    def _format_field_value(self, value: str, field_info: dict) -> str:
        """Formats a field value based on its properties (data-driven from JSON)."""
        datatype = field_info.get("datatype", "")

        # Date formatting based on datatype
        if datatype == "D":
            try:
                date_obj = datetime.strptime(value, "%Y%m%d")
                return date_obj.strftime("%d.%m.%Y")
            except ValueError:
                return f"{value} (invalid date format)"

        # Time formatting based on datatype
        if datatype == "U":
            try:
                if len(value) == 4:  # Format: HHMM
                    return f"{value[:2]}:{value[2:]}"
                elif len(value) == 6:  # Format: HHMMSS
                    return f"{value[:2]}:{value[2:4]}:{value[4:]}"
            except (ValueError, IndexError):
                pass

        # Check value mapping (for enum-like fields)
        if mapping_key := field_info.get("value_mapping"):
            mappings = self.field_definitions["value_mapping"].get(mapping_key, {})
            if value in mappings:
                mapped = mappings[value]
                if isinstance(mapped, dict):
                    return mapped.get("description", str(mapped))
                return str(mapped)

        # Numeric formatting for numeric types
        formatted = value
        if datatype == "N":
            if value.startswith("-.") and len(value) > 2 and value[2:].replace(".", "").isdigit():
                formatted = "-0," + value[2:]
            elif value.startswith(".") and len(value) > 1 and value[1:].replace(".", "").isdigit():
                formatted = "0," + value[1:]
            else:
                formatted = value.replace(".", ",")

        # Append unit if available
        if (unit := field_info.get("unit")) and unit:  # Only if unit is not empty
            formatted = f"{formatted} {unit}"

        return formatted


# UI components
scanner = QRCodeScanner()
input_field = None  # Global variable for the input field


@ui.refreshable
def status_area():
    """Displays the status message."""
    with ui.card().classes("w-64"):
        ui.label("Status:").classes("text-bold")
        ui.label(scanner.status_message).classes("text-grey-7")


@ui.refreshable
def list_area():
    """Displays the scanned data."""
    if not scanner.scanned_code:
        return

    with ui.list().props("bordered separator").classes("w-full"):
        ui.item_label("Wöhler QR Code Data").props("header").classes("text-bold")
        ui.separator()

        data_lines = [line for line in scanner.scanned_code.split("\n") if line]

        if scanner.field_definitions:
            interpreted_data = scanner.parse_qr_data(data_lines)
            _display_interpreted_data(interpreted_data)
        else:
            _display_raw_data(data_lines)


def _display_interpreted_data(data: list[list[str | list]]) -> None:
    """Displays the interpreted data."""
    for element in data:
        if not isinstance(element, list) or len(element) != 2:
            continue

        title, content = element

        if isinstance(content, list):  # Section
            ui.item_label(title).props("header").classes("text-bold q-mt-md")
            ui.separator()
            for desc, value in content:
                with ui.item():
                    with ui.item_section().classes("w-3/5"):
                        ui.item_label(desc)
                    with ui.item_section().classes("w-2/5"):
                        ui.item_label(value)
        else:  # Single field
            with ui.item():
                with ui.item_section().classes("w-3/5"):
                    ui.item_label(title).classes("text-bold")
                with ui.item_section().classes("w-2/5"):
                    ui.item_label(content)


def _display_raw_data(data_lines: list[str]) -> None:
    """Displays the raw data."""
    ui.item_label("Scanned Data").props("header").classes("text-bold")
    ui.separator()
    for line in data_lines:
        with ui.item_section():
            ui.item_label(line)


def setup_ui():
    """Creates the user interface."""
    global input_field  # Declare input_field as global
    field_file = os.environ.get("FIELD_NAMES_FILE", "field_names.json")
    scanner.load_field_definitions(field_file)
    with ui.card():
        ui.markdown("## QR-Code Scanner Interface")
        with ui.row():
            with ui.card():
                input_field = ui.textarea(
                    label="Scan field",
                    placeholder="Scan now",
                    on_change=lambda e: handle_scan(e.value),
                )
                ui.button("Clear field", on_click=handle_clear)
            status_area()
        list_area()


def handle_scan(value: str) -> None:
    """Handles new scan input."""
    scanner.process_scan(value)
    status_area.refresh()
    list_area.refresh()


def handle_clear() -> None:
    """Handles clearing the input field."""
    scanner.clear_scan()
    input_field.set_value("")
    status_area.refresh()
    list_area.refresh()


# Application startup
if __name__ in {"__main__", "__mp_main__"}:
    setup_ui()
    ui.run()
