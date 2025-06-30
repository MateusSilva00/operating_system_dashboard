"""
File Info - Modelo responsável pela coleta de informações de arquivos e diretórios
Navega pelo sistema de arquivos e extrai metadados detalhados
"""

import grp
import os
import pwd
import stat
from datetime import datetime
from typing import Dict, List, Optional


class FileInfo:
    """
    Classe responsável por coletar informações detalhadas de arquivos e diretórios
    """

    def __init__(self):
        self._user_cache = {}
        self._group_cache = {}
        self._build_user_group_cache()

    def _build_user_group_cache(self):
        """Constrói cache de usuários e grupos para melhor performance"""
        try:
            # Cache de usuários
            for user in pwd.getpwall(): # Obtém todos os usuários do sistema
                self._user_cache[user.pw_uid] = user.pw_name
        except Exception:
            pass

        try:
            # Cache de grupos
            for group in grp.getgrall(): # Obtém todos os grupos do sistema
                self._group_cache[group.gr_gid] = group.gr_name
        except Exception:
            pass

    def _get_permissions_string(self, mode: int) -> str:
        """Converte modo octal para string de permissões (rwxrwxrwx)"""
        permissions = ""

        # Tipo do arquivo
        if stat.S_ISDIR(mode):
            permissions += "d"
        elif stat.S_ISLNK(mode):
            permissions += "l"
        elif stat.S_ISREG(mode):
            permissions += "-"
        elif stat.S_ISBLK(mode):
            permissions += "b"
        elif stat.S_ISCHR(mode):
            permissions += "c"
        elif stat.S_ISFIFO(mode):
            permissions += "p"
        elif stat.S_ISSOCK(mode):
            permissions += "s"
        else:
            permissions += "?"

        # Permissões do proprietário
        permissions += "r" if mode & stat.S_IRUSR else "-"
        permissions += "w" if mode & stat.S_IWUSR else "-"
        permissions += "x" if mode & stat.S_IXUSR else "-"

        # Permissões do grupo
        permissions += "r" if mode & stat.S_IRGRP else "-"
        permissions += "w" if mode & stat.S_IWGRP else "-"
        permissions += "x" if mode & stat.S_IXGRP else "-"

        # Permissões de outros
        permissions += "r" if mode & stat.S_IROTH else "-"
        permissions += "w" if mode & stat.S_IWOTH else "-"
        permissions += "x" if mode & stat.S_IXOTH else "-"

        return permissions

    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para formato legível"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def get_directory_contents(self, path: str) -> List[Dict]:
        """
        Obtém conteúdo de um diretório com informações detalhadas
        """
        contents = []

        try:
            entries = os.listdir(path)
            entries.sort(
                key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower())
            )

            for entry in entries:
                entry_path = os.path.join(path, entry)
                file_info = self.get_file_info(entry_path)
                if file_info:
                    contents.append(file_info)

        except (PermissionError, FileNotFoundError, OSError):
            pass

        return contents

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Obtém informações detalhadas de um arquivo ou diretório
        """
        try:
            stat_info = os.lstat(file_path)

            # Informações básicas
            file_info = {
                "name": os.path.basename(file_path),
                "path": file_path,
                "size": stat_info.st_size,
                "size_formatted": self._format_size(stat_info.st_size),
                "permissions": self._get_permissions_string(stat_info.st_mode),
                "permissions_octal": oct(stat_info.st_mode)[-3:],
                "owner": self._user_cache.get(stat_info.st_uid, str(stat_info.st_uid)),
                "group": self._group_cache.get(stat_info.st_gid, str(stat_info.st_gid)),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "accessed": datetime.fromtimestamp(stat_info.st_atime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "created": datetime.fromtimestamp(stat_info.st_ctime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "is_directory": stat.S_ISDIR(stat_info.st_mode),
                "is_link": stat.S_ISLNK(stat_info.st_mode),
                "inode": stat_info.st_ino,
                "links": stat_info.st_nlink,
            }

            # Se for link simbólico, obtém o destino
            if file_info["is_link"]:
                try:
                    file_info["link_target"] = os.readlink(file_path)
                except OSError:
                    file_info["link_target"] = "?"

            # Tipo do arquivo
            if file_info["is_directory"]:
                file_info["type"] = "Diretório"
            elif file_info["is_link"]:
                file_info["type"] = "Link"
            else:
                # Determina tipo por extensão
                _, ext = os.path.splitext(file_info["name"])
                if ext:
                    file_info["type"] = f"Arquivo {ext.upper()[1:]}"
                else:
                    file_info["type"] = "Arquivo"

            return file_info

        except (OSError, PermissionError):
            return None

    def get_directory_tree(self, root_path: str, max_depth: int = 3) -> Dict:
        """
        Constrói árvore de diretórios limitada por profundidade
        """
        
        def build_tree(path: str, depth: int) -> Dict:
            if depth > max_depth:
                return {"name": os.path.basename(path), "path": path, "children": []}

            tree_node = {
                "name": os.path.basename(path) or path,
                "path": path,
                "children": [],
            }

            try:
                entries = [
                    e
                    for e in os.listdir(path)
                    if os.path.isdir(os.path.join(path, e)) and not e.startswith(".")
                ]
                entries.sort()

                for entry in entries:
                    child_path = os.path.join(path, entry)
                    child_node = build_tree(child_path, depth + 1)
                    tree_node["children"].append(child_node)

            except (PermissionError, FileNotFoundError):
                pass

            return tree_node

        return build_tree(root_path, 0)

    def search_files(
        self, directory: str, pattern: str, max_results: int = 100
    ) -> List[Dict]:
        """
        Busca arquivos por padrão no nome
        """
        results = []
        pattern_lower = pattern.lower()

        try:
            for root, dirs, files in os.walk(directory):
                # Limita busca em diretórios ocultos
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                for file in files:
                    if len(results) >= max_results:
                        break

                    if pattern_lower in file.lower():
                        file_path = os.path.join(root, file)
                        file_info = self.get_file_info(file_path)
                        if file_info:
                            results.append(file_info)

                if len(results) >= max_results:
                    break

        except (PermissionError, OSError):
            pass

        return results


if __name__ == "__main__":
    file_info = FileInfo()

    # Teste: listar conteúdo do diretório atual
    contents = file_info.get_directory_contents(".")
    for item in contents[:5]:
        print(
            f"{item['permissions']} {item['owner']} {item['size_formatted']} {item['name']}"
        )
