import os
import requests
import time
import flet as ft
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

def main(page: ft.Page):
    page.title = "Hub da Formula E"
    page.window.width = 450
    page.window.height = 700
    page.window.maximizable = False
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    load_dotenv()  # Carrega as variáveis de ambiente
    apiKey = os.getenv("API_KEY")  # Atribui o valor da variável de ambiente API_KEY à variável apiKey
    try:
        seasons = get_seasons(apiKey)  # Chama a função get_seasons() e armazena o retorno na variável seasons
        seasonID = most_recent_season_ID(seasons)  # Chama a função most_recent_season_ID() e armazena o retorno na variável seasonID
        time.sleep(1)  # Aguarda 1 segundo
        stage_infos = get_stage_infos(apiKey, seasonID)
        closestEvent = closest_event(stage_infos)
        teams_win_probabilities = get_teams_win_probabilities(apiKey, seasonID)
    except requests.exceptions.HTTPError as error:
        fatal_error("Erro ao acessar a API", f"Ocorreu um erro ao acessar a API da Formula E\n\n{error}")
        return
    
    def reload_app(e): #Função para recarregar o app
        page.controls.clear()
        page.update()
        main(page) 
        
    def fechar_app(e): #Função para fechar o app
        page.window.destroy()
        
    def fatal_error(msg, error): #Função para exibir um erro fatal
        error_dialog = ft.AlertDialog(
            title=ft.Text(msg),
            content=ft.Text(error),
            actions=[ft.TextButton("Fechar App", on_click=fechar_app), ft.TextButton("Recarregar App", on_click=reload_app)]
        )
        page.overlay.append(error_dialog)
        error_dialog.open = True
        page.update()
    
    def check_teams(): #Função para verificar se há equipes cadastradas
        teams = stage_infos.get('teams') 
        if teams:  # Verifica se 'teams' existe e não é None ou vazio
            return [ft.dropdown.Option(team['name']) for team in teams]
        else:
            return [
                ft.dropdown.Option("Não há equipes cadastradas para essa temporada ainda", disabled=True)
            ]
    
    def show_probability(): #Função para exibir as probabilidades de vitória das equipes
        if(teams_win_probabilities == []):
            win_probabilities.content.content.controls.append(ft.Text(
                value="Muito Cedo para Previsões",
                size=24,
                text_align=ft.TextAlign.LEFT,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.ERROR
            ))
        else:
            for i, team in enumerate(teams_win_probabilities):
                win_probabilities.content.content.controls.append(ft.Text(value=(f"- {team['name']} - {team['probability']}%"), size=18, text_align=ft.TextAlign.LEFT, weight=ft.FontWeight.BOLD, color=ft.colors.PRIMARY))
        
    def default_text(text, color=ft.colors.SECONDARY, weight=ft.FontWeight.W_500):
        return ft.Text(
            value=text,
            size=18,
            text_align=ft.TextAlign.LEFT,
            color=color,
            weight=weight
        )
        
    def default_title(text):
        return ft.Text(
            value=text,
            size=24,
            text_align=ft.TextAlign.START,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.SECONDARY
        )
        
    
    def events_infos(title, text):
        return ft.Column(controls=[default_text(title, ft.colors.INVERSE_SURFACE, ft.FontWeight.BOLD), default_text(text)])
        
    def create_team_rows(title, text):
        return ft.Row(
            controls=[default_text(title, ft.colors.INVERSE_SURFACE, ft.FontWeight.BOLD), default_text(text)],
            alignment=ft.MainAxisAlignment.START,
        )
        
        
    def verify_event():
        if  closestEvent == [] or closestEvent['id'] == None:
            return [
                ft.Text(
                    value="Não há eventos agendados ou está ocorrendo a transição de temporadas",
                    size=24,
                    text_align=ft.TextAlign.LEFT,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.ERROR
                )
            ]
        else:
            return [
                events_infos("Data e Hora: ", closestEvent['scheduled'].strftime('%d/%m/%Y %H:%M')),
                events_infos("Local: ", closestEvent['venue']['name']),
                events_infos("Cidade: ", closestEvent['venue']['city']),
                events_infos("País: ", closestEvent['venue']['country']),
            ]
    
    def selecionar_equipe(e, teams_container):
        teams_container.controls.clear()
        for team in stage_infos['teams']:
            if team['name'] == e.control.value:
                selected_team = team
                break
        team_result = selected_team['result']
        team_itens = [
            ("Nome: ", selected_team['name']),
            ("País: ", selected_team['nationality']),
            ("Pontos nessa temporada: ", team_result.get('points', '0')),
            ("Posição no campeonato: ", f"{team_result.get('position', 'N/A')}º lugar"),
            ("Vitórias: ", team_result.get('wins', '0')),
            ("Pódios: ", team_result.get('podiums', '0')),
            ("Voltas mais rápidas: ", team_result.get('fastest_laps', '0')),
            ("Pole Positions: ", team_result.get('pole_positions', '0')),
        ]
        for item in team_itens:
            teams_container.controls.append(create_team_rows(item[0], item[1]))
        teams_container.controls.append(ft.Text(
            value="Pilotos:",
            size=20,
            text_align=ft.TextAlign.LEFT,
            color=ft.colors.INVERSE_SURFACE,
            weight=ft.FontWeight.BOLD
        ))
        for driver in selected_team['competitors']:
            driver_result = driver['result']
            teams_container.controls.append(ft.Text(
                value=f"{driver_result.get('position', 'N/A')}º lugar - {driver_result.get('car_number', 'N/A')} - {' '.join(reversed(driver['name'].split(', ')))} - {driver['nationality']}",
                size=18,
                text_align=ft.TextAlign.LEFT,
                color=ft.colors.SECONDARY,
                weight=ft.FontWeight.W_500
            ))
        teams_container.update()
    
    def clear_stack(): #Função para limpar o container principal
        _stack_main.controls.clear()
        _stack_main.update()
        
    def on_page_resize(e): #Função para redimensionar os containers de acordo com o tamanho da janela
        next_event.height = page.window.height - 140
        teams.height = page.window.height - 140
        win_probabilities.height = page.window.height - 140
        page.update()  # Atualiza a página para aplicar as mudanças
    
    page.on_resized = on_page_resize
    
    def render_next_event(): #Função para renderizar a página de próximo evento
        _stack_main.controls.append(next_event)
        page.update()
        next_event.content = ft.Container(
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    default_title("Próximo Evento da Formula E"),
                    ft.Divider(height=10, thickness=2),
                    ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        controls=verify_event()
                    )
                ]
            ),
            padding=20,
            border_radius=15,
            expand=True
        )
        
    def render_teams(): #Função para renderizar a página de equipes
        _stack_main.controls.append(teams)
        teams_container = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            scroll= "always"
        )
        teams.content = ft.Container(
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    default_title("Equipes da Formula E"),
                    ft.Divider(height=10, thickness=2),  # Adicionando um divisor
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Dropdown(
                                label="Selecione uma equipe",
                                options=check_teams(),  # Aqui usamos um 'for' para criar as opções
                                on_change=lambda e: selecionar_equipe(e, teams_container)  # Função que será chamada quando o valor do Dropdown mudar
                            ),
                            ft.Container(height=20)
                        ]
                    ),
                    teams_container
                ]
            ),
            padding=20,
            border_radius=15,
            expand=True,
        )
        
    def render_win_probabilities(): #Função para renderizar a página de probabilidade de vitória
        _stack_main.controls.append(win_probabilities)
        win_probabilities.content = ft.Container(
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    default_title("Probabilidade de Vitória das Equipes"),
                    ft.Divider(height=10, thickness=2),  # Adicionando um divisor
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        scroll=ft.ScrollMode.AUTO,
                    )
                ]
            ),
            padding=20,
            border_radius=15,
            expand=True
        )
        show_probability()
        
    def navHandler(e): #Função para mudar de página
        selected_index = e.control.selected_index
        page.update()
        clear_stack() 
        if selected_index == 0:
            render_next_event() #Renderiza a página de próximo evento
        elif selected_index == 1:
            render_teams() #Renderiza a página de equipes
        elif selected_index == 2:
            render_win_probabilities() #Renderiza a página de probabilidade de vitória
        page.update()
        
        
    page.navigation_bar = ft.NavigationBar( #Barra de navegação
        on_change=navHandler,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.ACCESS_TIME_FILLED, label="Próximo Evento"),
            ft.NavigationBarDestination(icon=ft.icons.GROUPS, label="Equipes"),
            ft.NavigationBarDestination(icon=ft.icons.PERCENT, label="Chance de Vitória"),
        ]
    )
    
    def default_container(text): #Container padrão para otimizar a criação de containers
        return ft.Container(
            border_radius=10,
            alignment=ft.alignment.center,
            content=ft.Text(text),
            expand=True
        )    
    
    next_event = default_container("Próximo Evento")
    teams = default_container("Equipes")
    win_probabilities = default_container("Probabilidade de Vitória")
        
    _main = ft.Container( #Container principal
        width=450,
        alignment=ft.alignment.center,
        expand=True,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    value="Bem-vindo ao Hub da Formula E",
                    size=24,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    value="Selecione uma opção no menu abaixo para continuar",
                    text_align=ft.TextAlign.CENTER,
                    size=18
                )
            ]
        )  
    )
    
    _stack_main = ft.Stack(
        controls=[
            _main
        ]    
    )

    page.add(_stack_main)
    
def most_recent_season_ID(seasons):  # Retorna o ID da temporada mais recente
    return seasons["stages"][0]["id"] 

def get_seasons(apiKey):  # Retorna um objeto com todas as temporadas
    url = f"https://api.sportradar.com/formulae/trial/v2/pt/seasons.json?api_key={apiKey}"  # Define a URL da API
    headers = {"accept": "application/json"}  # Define o cabeçalho da requisição
    response = requests.get(url, headers=headers)  # Faz a requisição GET
    response.raise_for_status()  # Levanta exceção para status de erro HTTP
    return response.json()  # Converte o JSON para um objeto

def get_stage_infos(apiKey, seasonID):  # Retorna um objeto com as equipes
    url = f"https://api.sportradar.com/formulae/trial/v2/pt/sport_events/{seasonID}/summary.json?api_key={apiKey}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if datetime.fromisoformat(data['stage']['scheduled_end']) < datetime.now(timezone.utc):
        data['stage']['id'] = None
    return data['stage']  # Retorna o objeto com as equipes

def get_teams_win_probabilities(apiKey, seasonID):  # Retorna um objeto com as probabilidades de vitória das equipes
    url = f"https://api.sportradar.com/formulae/trial/v2/pt/sport_events/{seasonID}/probabilities.json?api_key={apiKey}"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    try:
        return data['probabilities']['markets'][0]['outcomes']
    except (KeyError, IndexError):
        return []

def closest_event(events):
    timezone_br = timezone(timedelta(hours=-3))
    # Converte a data de string para datetime e ajusta o fuso horário para o horário de Brasília
    if events['id'] == None: #verifica se o evento está ocorrendo
       return []
    else:
        for stage in events['stages']:
            stage['scheduled'] = datetime.fromisoformat(stage["scheduled"]).astimezone(timezone_br)
        events_sorted = sorted(events['stages'], key=lambda x: x["scheduled"])  # Ordena os eventos da data mais próxima para a mais distante
        now = datetime.now(timezone_br)  # Pega a data e hora atual
        # Encontra a data mais próxima de acontecer
        closest_event = min(events_sorted, key=lambda x: (x["scheduled"] - now).total_seconds() if x["scheduled"] > now else float('inf'))
        # Retorna o evento mais próximo de acontecer
        return closest_event

ft.app(target=main)