class LabelBuilder:
    @staticmethod
    def _mm(valor): 
        return int(valor * 8)

    @classmethod
    def gerar_etiqueta_padrao(cls, dados_etiquetas, layout):
        pos_x = [1.5, 37.0, 71.8]
        cmd = [b"SIZE 105 mm, 22 mm\n", b"GAP 2 mm, 0\n", b"DIRECTION 1\n", b"CODEPAGE 1252\n", b"CLS\n"]

        for i, x_mm in enumerate(pos_x):
            if i >= len(dados_etiquetas): break
            dados = dados_etiquetas[i]
            x_base, y_base = cls._mm(x_mm), cls._mm(0.5)
            y_inicio = y_base + cls._mm(20) 
            
            for t in layout.get("textos", []):
                valor = str(dados.get(t["campo"], ""))
                rot, bld = t.get("rotacao", 270), t.get("bold", 0)
                
                linhas = []
                if t.get("tipo") == "bloco_inteligente":
                    l1, l2 = t["max_chars_normal"], t["max_chars_pequena"]
                    if valor[:l1]: linhas.append({"texto": valor[:l1], "fonte": t["fonte_normal"], "passo": 0})
                    if valor[l1:l1+l2]: linhas.append({"texto": valor[l1:l1+l2], "fonte": t["fonte_pequena"], "passo": t.get("passo_x_mm", 0)})
                else:
                    linhas.append({"texto": valor, "fonte": t["fonte"], "passo": 0})
                
                for idx, linha in enumerate(linhas):
                    px = x_base + cls._mm(t["x_mm"] + (linha.get("passo", 0) * idx))
                    py = y_inicio + cls._mm(t["y_mm"])
                    if bld > 0: cmd.append(f"SET BOLD {bld}\n".encode('windows-1252', errors='ignore'))
                    cmd.append(f"TEXT {px},{py},\"{linha['fonte']}\",{rot},1,1,\"{linha['texto']}\"\n".encode('windows-1252', errors='ignore'))
                    if bld > 0: cmd.append(b"SET BOLD 0\n")
                
            if "qrcode" in layout:
                qr = layout["qrcode"]
                qx, qy = x_base + cls._mm(qr["x_mm"]), y_base + cls._mm(qr["y_mm"])
                cmd.append(f"QRCODE {qx},{qy},M,{qr['tamanho']},A,{qr['rotacao']},\"{dados.get(qr['campo'], '')}\"\n".encode('windows-1252', errors='ignore'))

        cmd.append(b"PRINT 1\n")
        return b"".join(cmd)