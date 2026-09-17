import customtkinter
import yt_dlp
import threading
import queue
from tkinter import filedialog
import os
import sys

customtkinter.set_appearance_mode("dark")

# 1. Iniciamos a variável vazia em vez de um caminho padrão
pasta_destino = ""

fila_downloads = queue.Queue()
download_ativo = False

def selecionar_pasta():
    global pasta_destino
    pasta_selecionada = filedialog.askdirectory()
    if pasta_selecionada:
        pasta_destino = pasta_selecionada
        label_pasta.configure(text=f"Destino: {pasta_destino}")

def hook_progresso(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        baixado = d.get('downloaded_bytes', 0)
        
        if total > 0:
            progresso = baixado / total
            barra_progresso.set(progresso)
            label_status.configure(text=f"Baixando: {int(progresso * 100)}%", text_color="yellow")
            
    elif d['status'] == 'finished':
        label_status.configure(text="Processando arquivo final...", text_color="orange")

def alterar_estado_qualidade(escolha):
    if escolha == "Áudio (MP3)":
        menu_qualidade.configure(state="disabled")
    else:
        menu_qualidade.configure(state="normal")

def baixar_video_youtube(url, formato_escolhido, qualidade_escolhida, baixar_playlist):
    opcoes_base = {
        'outtmpl': f'{pasta_destino}/%(title)s.%(ext)s',
        'progress_hooks': [hook_progresso],
        'noplaylist': not baixar_playlist, 
    }

    if formato_escolhido == "Áudio (MP3)":
        opcoes = opcoes_base.copy()
        opcoes.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
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
        label_status.configure(text="Iniciando...", text_color="yellow")
        
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
            
        label_status.configure(text="Pronto para o próximo!", text_color="green")
        barra_progresso.set(1)
    except Exception as e:
        label_status.configure(text="Erro no download anterior.", text_color="red")
        print(e) 

def worker_fila():
    global download_ativo
    download_ativo = True
    
    while not fila_downloads.empty():
        tarefa = fila_downloads.get()
        url, formato, qualidade, quer_playlist = tarefa
        
        label_fila.configure(text=f"Vídeos aguardando na fila: {fila_downloads.qsize()}")
        baixar_video_youtube(url, formato, qualidade, quer_playlist)
        
    download_ativo = False
    label_status.configure(text="Todos os downloads da fila foram concluídos!", text_color="green")
    label_fila.configure(text="Vídeos aguardando na fila: 0")

def adicionar_a_fila():
    # 2. Trava de segurança: Verifica se a pasta foi escolhida antes de fazer qualquer coisa
    if pasta_destino == "":
        label_status.configure(text="Atenção: Escolha uma pasta de destino primeiro.", text_color="red")
        return # Interrompe a função aqui e não adiciona à fila

    url = entrada_url.get()
    formato = menu_formato.get() 
    qualidade = menu_qualidade.get()
    quer_playlist = checkbox_playlist.get() == 1 
    
    if url:
        fila_downloads.put((url, formato, qualidade, quer_playlist))
        entrada_url.delete(0, 'end')
        label_fila.configure(text=f"Vídeos aguardando na fila: {fila_downloads.qsize()}")
        
        global download_ativo
        if not download_ativo:
            thread = threading.Thread(target=worker_fila, daemon=True)
            thread.start()
    else:
        label_status.configure(text="Por favor, insira um link válido.", text_color="red")

app = customtkinter.CTk()
app.geometry("500x650")
app.title("Baixador de Vídeos e Áudios do YouTube")

if sys.platform == "win32" and os.path.exists("icone.ico"):
    app.iconbitmap("icone.ico")

label_titulo = customtkinter.CTkLabel(app, text="Cole a URL do vídeo do YouTube aqui:")
label_titulo.pack(pady=(20, 5))

entrada_url = customtkinter.CTkEntry(app, width=350)
entrada_url.pack(pady=10)

checkbox_playlist = customtkinter.CTkCheckBox(app, text="Baixar playlist inteira (se houver)")
checkbox_playlist.pack(pady=5)

frame_menus = customtkinter.CTkFrame(app, fg_color="transparent")
frame_menus.pack(pady=10)

label_formato = customtkinter.CTkLabel(frame_menus, text="Formato:")
label_formato.grid(row=0, column=0, padx=10, pady=5)
menu_formato = customtkinter.CTkOptionMenu(frame_menus, values=["Vídeo (MP4)", "Áudio (MP3)"], command=alterar_estado_qualidade)
menu_formato.grid(row=1, column=0, padx=10)

label_qualidade = customtkinter.CTkLabel(frame_menus, text="Qualidade:")
label_qualidade.grid(row=0, column=1, padx=10, pady=5)
menu_qualidade = customtkinter.CTkOptionMenu(frame_menus, values=["Melhor Qualidade", "1080p", "720p", "480p"])
menu_qualidade.grid(row=1, column=1, padx=10)

botao_pasta = customtkinter.CTkButton(app, text="Escolher Pasta de Destino", command=selecionar_pasta, fg_color="gray")
botao_pasta.pack(pady=20)

# 3. Atualizamos o texto inicial para refletir que não há pasta escolhida
label_pasta = customtkinter.CTkLabel(app, text="Destino: Nenhuma pasta selecionada", font=("Arial", 11))
label_pasta.pack(pady=(0, 10))

botao_baixar = customtkinter.CTkButton(app, text="Adicionar à Fila", command=adicionar_a_fila)
botao_baixar.pack(pady=10)

label_fila = customtkinter.CTkLabel(app, text="Vídeos aguardando na fila: 0", font=("Arial", 11))
label_fila.pack(pady=5)

barra_progresso = customtkinter.CTkProgressBar(app, width=350)
barra_progresso.pack(pady=10)
barra_progresso.set(0)

label_status = customtkinter.CTkLabel(app, text="")
label_status.pack(pady=10)

app.mainloop()