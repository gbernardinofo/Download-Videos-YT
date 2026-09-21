import customtkinter
import yt_dlp
import threading
from tkinter import filedialog
import os
import sys

customtkinter.set_appearance_mode("dark")

pasta_destino = ""
fila_downloads = []
download_ativo = False

def selecionar_pasta():
    global pasta_destino
    pasta_selecionada = filedialog.askdirectory()
    if pasta_selecionada:
        pasta_destino = pasta_selecionada
        label_pasta.configure(text=f"Destino: {pasta_destino}")

def formatar_tempo(segundos):
    if not segundos:
        return "00:00"
    m, s = divmod(int(segundos), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def hook_progresso(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        baixado = d.get('downloaded_bytes', 0)
        
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)
        
        speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else "-- MB/s"
        eta_str = formatar_tempo(eta) if eta else "--:--"
        
        if total > 0:
            progresso = baixado / total
            barra_progresso.set(progresso)
            label_status.configure(
                text=f"Baixando: {int(progresso * 100)}% | {speed_str} | ETA: {eta_str}", 
                text_color="yellow"
            )
            
    elif d['status'] == 'finished':
        label_status.configure(text="Processando arquivo final...", text_color="orange")

def atualizar_interface_fila():
    for widget in frame_fila.winfo_children():
        widget.destroy()

    for idx, item in enumerate(fila_downloads):
        frame_item = customtkinter.CTkFrame(frame_fila, fg_color="#2b2b2b")
        frame_item.pack(fill="x", pady=2, padx=5)

        lbl = customtkinter.CTkLabel(
            frame_item, 
            text=f"{idx + 1}. {item['url'][:35]}... ({item['formato']})", 
            anchor="w"
        )
        lbl.pack(side="left", padx=5, expand=True, fill="x")

        btn_remover = customtkinter.CTkButton(
            frame_item, 
            text="X", 
            width=25, 
            height=25, 
            fg_color="red", 
            hover_color="darkred",
            command=lambda i=idx: remover_da_fila(i)
        )
        btn_remover.pack(side="right", padx=5, pady=2)

    label_count_fila.configure(text=f"Vídeos na fila: {len(fila_downloads)}")

def remover_da_fila(index):
    if 0 <= index < len(fila_downloads):
        fila_downloads.pop(index)
        atualizar_interface_fila()

def alterar_estado_qualidade(escolha):
    if escolha == "Áudio (MP3)":
        menu_qualidade.configure(values=["320 kbps (Melhor)", "192 kbps (Padrão)", "128 kbps (Leve)"])
        menu_qualidade.set("192 kbps (Padrão)")
    else:
        menu_qualidade.configure(values=["Melhor Qualidade", "1080p", "720p", "480p"])
        menu_qualidade.set("Melhor Qualidade")

def baixar_video_youtube(tarefa):
    url = tarefa['url']
    formato_escolhido = tarefa['formato']
    qualidade_escolhida = tarefa['qualidade']
    baixar_playlist = tarefa['playlist']

    opcoes_base = {
        'outtmpl': f'{pasta_destino}/%(title)s.%(ext)s',
        'progress_hooks': [hook_progresso],
        'noplaylist': not baixar_playlist, 
    }

    if formato_escolhido == "Áudio (MP3)":
        bitrate = qualidade_escolhida.split()[0]
        opcoes = opcoes_base.copy()
        opcoes.update({
            'format': 'bestaudio/best',
            'writethumbnail': True,  # Necessário para embutir a capa
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': bitrate},
                {'key': 'EmbedThumbnail'},
                {'key': 'FFmpegMetadata'},
            ],
        })
    else:
        if qualidade_escolhida == "1080p":
            filtro_qualidade = 'bestvideo[height<=1080]+bestaudio/best'
        elif qualidade_escolhida == "720p":
            filtro_qualidade = 'bestvideo[height<=720]+bestaudio/best'
        elif qualidade_escolhida == "480p":
            filtro_qualidade = 'bestvideo[height<=480]+bestaudio/best'
        else:
            filtro_qualidade = 'bestvideo+bestaudio/best'
            
        opcoes = opcoes_base.copy()
        opcoes.update({
            'format': filtro_qualidade, 
            'merge_output_format': 'mp4'
        })
    
    try:
        barra_progresso.set(0)
        label_status.configure(text="Iniciando download...", text_color="yellow")
        
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])

        # Remove o ficheiro .jpg restante caso tenha ficado na pasta
        for ficheiro in os.listdir(pasta_destino):
            if ficheiro.endswith(".jpg") or ficheiro.endswith(".webp"):
                caminho = os.path.join(pasta_destino, ficheiro)
                try:
                    os.remove(caminho)
                except Exception:
                    pass
            
        label_status.configure(text="Concluído!", text_color="green")
        barra_progresso.set(1)
    except Exception as e:
        label_status.configure(text="Erro no download.", text_color="red")
        print(e) 

def worker_fila():
    global download_ativo
    download_ativo = True
    
    while len(fila_downloads) > 0:
        tarefa = fila_downloads.pop(0)
        app.after(0, atualizar_interface_fila)
        baixar_video_youtube(tarefa)
        
    download_ativo = False
    label_status.configure(text="Todos os downloads foram concluídos!", text_color="green")
    app.after(0, atualizar_interface_fila)

def adicionar_a_fila():
    if pasta_destino == "":
        label_status.configure(text="Atenção: Escolha uma pasta de destino primeiro.", text_color="red")
        return

    url = entrada_url.get().strip()
    if not url:
        label_status.configure(text="Por favor, insira uma URL válida.", text_color="red")
        return

    tarefa = {
        'url': url,
        'formato': menu_formato.get(),
        'qualidade': menu_qualidade.get(),
        'playlist': checkbox_playlist.get() == 1
    }

    fila_downloads.append(tarefa)
    atualizar_interface_fila()
    
    entrada_url.delete(0, 'end')

    global download_ativo
    if not download_ativo:
        threading.Thread(target=worker_fila, daemon=True).start()

# --- INTERFACE GRÁFICA ---
app = customtkinter.CTk()
app.geometry("500x650")
app.title("Baixador do YouTube - Avançado")

if sys.platform == "win32" and os.path.exists("icone.ico"):
    app.iconbitmap("icone.ico")

label_titulo = customtkinter.CTkLabel(app, text="Cole a URL do vídeo do YouTube aqui:")
label_titulo.pack(pady=(20, 5))

entrada_url = customtkinter.CTkEntry(app, width=380)
entrada_url.pack(pady=10)

checkbox_playlist = customtkinter.CTkCheckBox(app, text="Baixar playlist inteira (se houver)")
checkbox_playlist.pack(pady=10)

frame_menus = customtkinter.CTkFrame(app, fg_color="transparent")
frame_menus.pack(pady=5)

label_formato = customtkinter.CTkLabel(frame_menus, text="Formato:")
label_formato.grid(row=0, column=0, padx=10, pady=2)
menu_formato = customtkinter.CTkOptionMenu(frame_menus, values=["Vídeo (MP4)", "Áudio (MP3)"], command=alterar_estado_qualidade)
menu_formato.grid(row=1, column=0, padx=10)

label_qualidade = customtkinter.CTkLabel(frame_menus, text="Qualidade:")
label_qualidade.grid(row=0, column=1, padx=10, pady=2)
menu_qualidade = customtkinter.CTkOptionMenu(frame_menus, values=["Melhor Qualidade", "1080p", "720p", "480p"])
menu_qualidade.grid(row=1, column=1, padx=10)

botao_pasta = customtkinter.CTkButton(app, text="Escolher Pasta de Destino", command=selecionar_pasta, fg_color="gray")
botao_pasta.pack(pady=15)

label_pasta = customtkinter.CTkLabel(app, text="Destino: Nenhuma pasta selecionada", font=("Arial", 11))
label_pasta.pack(pady=(0, 5))

botao_baixar = customtkinter.CTkButton(app, text="Adicionar à Fila", command=adicionar_a_fila)
botao_baixar.pack(pady=10)

label_count_fila = customtkinter.CTkLabel(app, text="Vídeos na fila: 0", font=("Arial", 11, "bold"))
label_count_fila.pack(pady=(10, 2))

frame_fila = customtkinter.CTkScrollableFrame(app, width=420, height=120)
frame_fila.pack(pady=5)

barra_progresso = customtkinter.CTkProgressBar(app, width=420)
barra_progresso.pack(pady=10)
barra_progresso.set(0)

label_status = customtkinter.CTkLabel(app, text="", font=("Arial", 11))
label_status.pack(pady=5)

app.mainloop()