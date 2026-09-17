import yt_dlp

def baixar_video_youtube(url, pasta_destino='./videos_baixados'):
    opcoes = {
        'outtmpl': f'{pasta_destino}/%(title)s.%(ext)s',
        
        # Tenta pegar o melhor vídeo e áudio separados. Se falhar, pega o melhor formato único.
        'format': 'bestvideo+bestaudio/best', 
        
        # Junta os arquivos (caso venham separados) num formato mp4
        'merge_output_format': 'mp4',
    }

    try:
        print(f"Iniciando o download do vídeo...")
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
            
        print("\nDownload concluído com sucesso!")
        
    except Exception as e:
        print(f"\nOcorreu um erro durante o download: {e}")

if __name__ == "__main__":
    url_video = input("Cole a URL do vídeo do YouTube aqui: ")
    baixar_video_youtube(url_video)