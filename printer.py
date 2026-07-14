from config import SISTEMA

if SISTEMA == "Windows":
    import win32print

class PrinterEngine:
    @staticmethod
    def enviar(porta_ou_nome, comandos_tspl):
        if SISTEMA == "Windows":
            hPrinter = win32print.OpenPrinter(porta_ou_nome)
            try:
                win32print.StartDocPrinter(hPrinter, 1, ("Etiquetas TSPL", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, comandos_tspl)
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
                win32print.ClosePrinter(hPrinter)
        else:
            with open(porta_ou_nome, 'wb') as impressora:
                impressora.write(comandos_tspl)

    @staticmethod
    def listar_impressoras_windows():
        if SISTEMA == "Windows":
            printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
            return [p[2] for p in printers]
        return []