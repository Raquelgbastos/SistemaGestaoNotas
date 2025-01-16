import pandas as pd
import mysql.connector
from typing import Dict, List, Optional
from datetime import datetime

class SistemaGestaoNotas:
    def __init__(self):
        self.alunos = {}  
        self.notas = {}   
        
        
        self.db_config = {
            "host": "localhost",
            "user": "Raquel",
            "password": "2012",
            "database": "gestao_notas"
        }

    def inserir_aluno(self, id_aluno: int, nome: str, ano: int, turma: str) -> bool:
        if id_aluno not in self.alunos:
            self.alunos[id_aluno] = {
                'nome': nome,
                'ano': ano,
                'turma': turma
            }
            self.notas[id_aluno] = {}
            return True
        return False

    def atualizar_aluno(self, id_aluno: int, nome: str = None, ano: int = None, turma: str = None) -> bool:
        if id_aluno in self.alunos:
            if nome:
                self.alunos[id_aluno]['nome'] = nome
            if ano:
                self.alunos[id_aluno]['idade'] = ano
            if turma:
                self.alunos[id_aluno]['turma'] = turma
            return True
        return False

    def eliminar_aluno(self, id_aluno: int) -> bool:
        if id_aluno in self.alunos:
            del self.alunos[id_aluno]
            del self.notas[id_aluno]
            return True
        return False

    def adicionar_nota(self, id_aluno: int, disciplina: str, nota: float) -> bool:
        if id_aluno in self.alunos:
            if disciplina not in self.notas[id_aluno]:
                self.notas[id_aluno][disciplina] = []
            if 0 <= nota <= 20:  
                self.notas[id_aluno][disciplina].append(nota)
                return True
        return False

    def filtrar_notas_disciplina(self, disciplina: str) -> Dict:
        notas_disciplina = {}
        for id_aluno, notas in self.notas.items():
            if disciplina in notas:
                notas_disciplina[id_aluno] = notas[disciplina]
        return notas_disciplina

    def eliminar_nota(self, id_aluno: int, disciplina: str, indice: int) -> bool:
        if (id_aluno in self.notas and 
            disciplina in self.notas[id_aluno] and 
            indice < len(self.notas[id_aluno][disciplina])):
            del self.notas[id_aluno][disciplina][indice]
            return True
        return False

    def calcular_media_disciplina(self, disciplina: str) -> float:
        todas_notas = []
        for notas_aluno in self.notas.values():
            if disciplina in notas_aluno:
                todas_notas.extend(notas_aluno[disciplina])
        return sum(todas_notas) / len(todas_notas) if todas_notas else 0

    def calcular_media_aluno(self, id_aluno: int) -> Dict[str, float]:
        if id_aluno in self.notas:
            medias = {}
            for disciplina, notas in self.notas[id_aluno].items():
                if notas:
                    medias[disciplina] = sum(notas) / len(notas)
            return medias
        return {}

    def calcular_media_turma(self, turma: str) -> float:
        notas_turma = []
        for id_aluno, dados in self.alunos.items():
            if dados['turma'] == turma:
                medias = self.calcular_media_aluno(id_aluno)
                if medias:
                    notas_turma.append(sum(medias.values()) / len(medias))
        return sum(notas_turma) / len(notas_turma) if notas_turma else 0

    def obter_extremos_aluno(self, id_aluno: int) -> Dict:
        if id_aluno in self.notas:
            extremos = {}
            for disciplina, notas in self.notas[id_aluno].items():
                if notas:
                    extremos[disciplina] = {
                        'maior': max(notas),
                        'menor': min(notas)
                    }
            return extremos
        return {}

    def obter_extremos_disciplina(self, disciplina: str) -> Dict:
        todas_notas = []
        for notas_aluno in self.notas.values():
            if disciplina in notas_aluno:
                todas_notas.extend(notas_aluno[disciplina])
        if todas_notas:
            return {
                'maior': max(todas_notas),
                'menor': min(todas_notas)
            }
        return {}

    def avaliar_aluno(self, id_aluno: int, media_aprovacao: float = 9.5) -> Dict:
        medias = self.calcular_media_aluno(id_aluno)
        if medias:
            media_final = sum(medias.values()) / len(medias)
            return {
                'media_final': media_final,
                'situacao': 'Aprovado' if media_final >= media_aprovacao else 'Reprovado',
                'medias_disciplinas': medias
            }
        return {}

    def gerar_relatorio_final(self) -> Dict:
        relatorio = {}
        for id_aluno, dados in self.alunos.items():
            relatorio[id_aluno] = {
                'dados': dados,
                'avaliacao': self.avaliar_aluno(id_aluno)
            }
        return relatorio

    def exportar_mysql(self) -> bool:
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alunos (
                    id_aluno INT PRIMARY KEY,
                    nome VARCHAR(255),
                    ano INT,
                    turma VARCHAR(50)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_aluno INT,
                    disciplina VARCHAR(255),
                    nota FLOAT,
                    FOREIGN KEY (id_aluno) REFERENCES alunos(id_aluno)
                )
            """)

            
            for id_aluno, dados in self.alunos.items():
                cursor.execute("""
                    INSERT INTO alunos (id_aluno, nome, ano, turma)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    nome = VALUES(nome),
                    ano = VALUES(ano),
                    turma = VALUES(turma)
                """, (id_aluno, dados['nome'], dados['ano'], dados['turma']))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro na exportação MySQL: {e}")
            return False

    def exportar_excel(self, nome_arquivo: str) -> bool:
        try:
            dados = []
            for id_aluno, aluno in self.alunos.items():
                linha = {
                    'ID': id_aluno,
                    'Nome': aluno['nome'],
                    'ano': aluno['ano'],
                    'Turma': aluno['turma']
                }
                medias = self.calcular_media_aluno(id_aluno)
                for disciplina, media in medias.items():
                    linha[f'Média {disciplina}'] = media
                dados.append(linha)
            
            df = pd.DataFrame(dados)
            df.to_excel(nome_arquivo, index=False)
            return True
        except Exception as e:
            print(f"Erro na exportação Excel: {e}")
            return False

    def importar_mysql(self) -> bool:
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM alunos")
            for (id_aluno, nome, ano, turma) in cursor:
                self.inserir_aluno(id_aluno, nome, ano, turma)

            cursor.execute("SELECT * FROM notas")
            for (_, id_aluno, disciplina, nota) in cursor:
                self.adicionar_nota(id_aluno, disciplina, nota)

            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro na importação MySQL: {e}")
            return False

    def importar_excel(self, nome_arquivo: str) -> bool:
        try:
            df = pd.read_excel(nome_arquivo)
            for _, row in df.iterrows():
                self.inserir_aluno(
                    int(row['ID']),
                    row['Nome'],
                    int(row['Ano']),
                    row['Turma']
                )
            return True
        except Exception as e:
            print(f"Erro na importação Excel: {e}")
            return False
        
        
    def consultar_aluno(self, id_aluno: int) -> Optional[Dict]:
        """Consulta os dados de um aluno específico."""
        return self.alunos.get(id_aluno, None)

    def executar_menu(self):
        while True:
            print("\n=== Sistema de Gestão de Notas ===")
            print("\n1. Gestão de Alunos")
            print("2. Gestão de Notas")
            print("3. Cálculo de Médias")
            print("4. Análise de Desempenho")
            print("5. Avaliação Final")
            print("6. Gestão de Dados")
            print("7. Sair")

            opcao = input("\nEscolha uma opção: ")

            if opcao == "1":
                while True:  
                    print("\n=== Gestão de Alunos ===")
                    print("1. Inserir Aluno")
                    print("2. Atualizar Aluno")
                    print("3. Eliminar Aluno")
                    print("4. Consultar Aluno")
                    print("5. Listar Todos os Alunos")
                    print("6. Voltar ao Menu Principal")
                
                    sub_opcao = input("Escolha uma opção: ")
                    
                    if sub_opcao == "1":
                        id_aluno = int(input("ID do aluno: "))
                        nome = input("Nome: ")
                        ano = int(input("Ano: "))
                        turma = input("Turma: ")
                        if self.inserir_aluno(id_aluno, nome, ano, turma):
                            print("Aluno inserido com sucesso!")
                        else:
                            print("Erro ao inserir aluno.")
                            
                    elif sub_opcao == "2":
                        id_aluno = int(input("ID do aluno: "))
                        print("\nDeixe em branco para manter o valor atual")
                        nome = input("Novo nome (ou Enter para manter): ")
                        ano_str = input("Novo ano (ou Enter para manter): ")
                        turma = input("Nova turma (ou Enter para manter): ")
                            
                        ano = int(ano_str) if ano_str.strip() else None
                        nome = nome if nome.strip() else None
                        turma = turma if turma.strip() else None
                            
                        if self.atualizar_aluno(id_aluno, nome, ano, turma):
                            print("Aluno atualizado com sucesso!")
                        else:
                            print("Erro ao atualizar aluno.")
                        
                    elif sub_opcao == "3":
                        id_aluno = int(input("ID do aluno a eliminar: "))
                        if self.eliminar_aluno(id_aluno):
                            print("Aluno eliminado com sucesso!")
                        else:
                            print("Erro ao eliminar aluno.")
                        
                    elif sub_opcao == "4":
                        id_aluno = int(input("ID do aluno para consulta: "))
                        aluno = self.consultar_aluno(id_aluno)
                        if aluno:
                            print("\n=== Dados do Aluno ===")
                            print(f"ID: {id_aluno}")
                            print(f"Nome: {aluno['nome']}")
                            print(f"Ano: {aluno['ano']}")
                            print(f"Turma: {aluno['turma']}")
                            
                            if id_aluno in self.notas and self.notas[id_aluno]:
                                print("\nNotas:")
                                for disciplina, notas in self.notas[id_aluno].items():
                                    print(f"{disciplina}: {notas}")
                        else:
                            print("Aluno não encontrado.")
                        
                    elif sub_opcao == "5":
                        if self.alunos:
                            print("\n=== Lista de Todos os Alunos ===")
                            for id_aluno, dados in self.alunos.items():
                                print(f"\nID: {id_aluno}")
                                print(f"Nome: {dados['nome']}")
                                print(f"Ano: {dados['ano']}")
                                print(f"Turma: {dados['turma']}")
                        else:
                            print("Erro! Não há Alunos Registados!")
                    
                    elif sub_opcao == "6":
                        break
                    
                    else:
                        print("Opção inválida!")

            elif opcao == "2":
                while True:  
                    print("\n=== Gestão de Notas ===")
                    print("1. Adicionar Nota")
                    print("2. Filtrar Notas por Disciplina")
                    print("3. Eliminar Nota")
                    print("4. Voltar ao Menu Principal")
                    sub_opcao = input("Escolha uma opção: ")
                    
                    if sub_opcao == "1":
                        id_aluno = int(input("ID do aluno: "))
                        disciplina = input("Disciplina: ")
                        nota = float(input("Nota: "))
                        if self.adicionar_nota(id_aluno, disciplina, nota):
                            print("Nota adicionada com sucesso!")
                        else:
                            print("Erro ao adicionar nota.")
                    
                    elif sub_opcao == "2":
                        disciplina = input("Digite a disciplina para filtrar: ")
                        notas_filtradas = self.filtrar_notas_disciplina(disciplina)
                        if notas_filtradas:
                            print(f"\nNotas de {disciplina}:")
                            for id_aluno, notas in notas_filtradas.items():
                                print(f"Aluno ID {id_aluno}: {notas}")
                        else:
                            print(f"Não foram encontradas notas para a disciplina {disciplina}")
                    
                    elif sub_opcao == "3":
                        id_aluno = int(input("ID do aluno: "))
                        disciplina = input("Disciplina: ")
                        indice = int(input("Índice da nota a eliminar: "))
                        if self.eliminar_nota(id_aluno, disciplina, indice):
                            print("Nota eliminada com sucesso!")
                        else:
                            print("Erro ao eliminar nota.")

                    elif sub_opcao == "4":
                        break

                    else:
                        print("Opção inválida!")

            elif opcao == "3":
                while True:  
                    print("\n=== Cálculo de Médias ===")
                    print("1. Média por Disciplina")
                    print("2. Média por Aluno")
                    print("3. Média por Turma")
                    print("4. Voltar ao Menu Principal")
                    
                    sub_opcao = input("Escolha uma opção: ")
                    
                    if sub_opcao == "1":
                        disciplina = input("Digite a disciplina: ")
                        media = self.calcular_media_disciplina(disciplina)
                        if media > 0:
                            print(f"Média da disciplina {disciplina}: {media:.2f}")
                        else:
                            print(f"Não foram encontradas notas para a disciplina {disciplina}")

                    elif sub_opcao == "2":
                        id_aluno = int(input("ID do aluno: "))
                        medias = self.calcular_media_aluno(id_aluno)
                        if medias:
                            print(f"\nMédias do aluno {id_aluno}:")
                            for disciplina, media in medias.items():
                                print(f"{disciplina}: {media:.2f}")
                        else:
                            print("Aluno não encontrado ou sem notas registradas.")

                    elif sub_opcao == "3":
                        turma = input("Digite a turma: ")
                        media = self.calcular_media_turma(turma)
                        if media > 0:
                            print(f"Média da turma {turma}: {media:.2f}")
                        else:
                            print(f"Não foram encontradas notas para a turma {turma}")

                    elif sub_opcao == "4":
                        break

                    else:
                        print("Opção inválida!")

            elif opcao == "4":
                while True:  
                    print("\n=== Análise de Desempenho ===")
                    print("1. Extremos por Aluno")
                    print("2. Extremos por Disciplina")
                    print("3. Voltar ao Menu Principal")
                    
                    sub_opcao = input("Escolha uma opção: ")
                    
                    if sub_opcao == "1":
                        id_aluno = int(input("ID do aluno: "))
                        extremos = self.obter_extremos_aluno(id_aluno)
                        if extremos:
                            print(f"\nExtremos do aluno {id_aluno}:")
                            for disciplina, valores in extremos.items():
                                print(f"{disciplina}:")
                                print(f"  Maior nota: {valores['maior']}")
                                print(f"  Menor nota: {valores['menor']}")
                        else:
                            print("Aluno não encontrado ou sem notas registradas.")

                    elif sub_opcao == "2":
                        disciplina = input("Digite a disciplina: ")
                        extremos = self.obter_extremos_disciplina(disciplina)
                        if extremos:
                            print(f"\nExtremos da disciplina {disciplina}:")
                            print(f"Maior nota: {extremos['maior']}")
                            print(f"Menor nota: {extremos['menor']}")
                        else:
                            print(f"Não foram encontradas notas para a disciplina {disciplina}")

                    elif sub_opcao == "3":
                        break

                    else:
                        print("Opção inválida!")

            elif opcao == "5":
                while True:  
                    print("\n=== Avaliação Final ===")
                    print("1. Avaliar Aluno")
                    print("2. Gerar Relatório Final")
                    print("3. Voltar ao Menu Principal")
                    
                    sub_opcao = input("Escolha uma opção: ")
                    
                    if sub_opcao == "1":
                        id_aluno = int(input("ID do aluno: "))
                        avaliacao = self.avaliar_aluno(id_aluno)
                        if avaliacao:
                            print(f"\nAvaliação do aluno {id_aluno}:")
                            print(f"Média Final: {avaliacao['media_final']:.2f}")
                            print(f"Situação: {avaliacao['situacao']}")
                            print("\nMédias por disciplina:")
                            for disciplina, media in avaliacao['medias_disciplinas'].items():
                                print(f"{disciplina}: {media:.2f}")
                        else:
                            print("Aluno não encontrado ou sem notas registradas.")

                    elif sub_opcao == "2":
                        relatorio = self.gerar_relatorio_final()
                        if relatorio:
                            print("\n=== Relatório Final ===")
                            for id_aluno, dados in relatorio.items():
                                print(f"\nAluno: {dados['dados']['nome']}")
                                print(f"ID: {id_aluno}")
                                print(f"Ano: {dados['dados']['ano']}")
                                print(f"Turma: {dados['dados']['turma']}")
                                if 'avaliacao' in dados and dados['avaliacao']:
                                    print(f"Média Final: {dados['avaliacao']['media_final']:.2f}")
                                    print(f"Situação: {dados['avaliacao']['situacao']}")
                        else:
                            print("Não há alunos registrados no sistema.")

                    elif sub_opcao == "3":
                        break

                    else:
                        print("Opção inválida!")

            elif opcao == "6":
                while True:  
                    print("\n=== Gestão de Dados ===")
                    print("1. Exportar para MySQL")
                    print("2. Exportar para Excel")
                    print("3. Importar de MySQL")
                    print("4. Importar de Excel")
                    print("5. Voltar ao Menu Principal")
                    
                    sub_opcao = input("Escolha uma opção: ")
                    
                    if sub_opcao == "1":
                        if self.exportar_mysql():
                            print("Dados exportados com sucesso para MySQL!")
                        else:
                            print("Erro ao exportar dados para MySQL.")

                    elif sub_opcao == "2":
                        nome_arquivo = input("Nome do arquivo Excel (ex: notas.xlsx): ")
                        if self.exportar_excel(nome_arquivo):
                            print(f"Dados exportados com sucesso para {nome_arquivo}!")
                        else:
                            print("Erro ao exportar dados para Excel.")

                    elif sub_opcao == "3":
                        if self.importar_mysql():
                            print("Dados importados com sucesso do MySQL!")
                        else:
                            print("Erro ao importar dados do MySQL.")

                    elif sub_opcao == "4":
                        nome_arquivo = input("Nome do arquivo Excel para importar: ")
                        if self.importar_excel(nome_arquivo):
                            print(f"Dados importados com sucesso de {nome_arquivo}!")
                        else:
                            print("Erro ao importar dados do Excel.")

                    elif sub_opcao == "5":
                        break

                    else:
                        print("Opção inválida!")

            elif opcao == "7":
                print("A sair...")
                break

            else:
                print("Opção inválida!")    
                
if __name__ == "__main__":
    sistema = SistemaGestaoNotas()
    sistema.executar_menu()