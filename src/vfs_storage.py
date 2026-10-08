import csv
import base64
import binascii


class VFSError(Exception):
    """Ошибка загрузки/сохранения VFS."""


class VFSStorage:
    """Виртуальная ФС в памяти. Плоский словарь:
    полный путь -> узел. Вложенность выражается
    через пути, а не через вложенные словари."""

    def __init__(self):
        """Инициализирует пустой словарь узлов
        и текущий каталог."""
        self.nodes = {
            '/': {'type': 'dir', 'owner': 'root', 'content': b''},
        }
        self.cwd = '/'

    def load(self, path):
        """Загружает VFS из CSV. Кидает VFSError."""
        self.nodes = {}
        try:
            self._read_csv(path)
        except FileNotFoundError:
            raise VFSError(f'файл не найден: {path}')
        except csv.Error as e:
            raise VFSError(f'неверный CSV-формат: {e}')

        if not self.nodes:
            raise VFSError('VFS пустая')
        if '/' not in self.nodes:
            self.nodes['/'] = {
                'type': 'dir', 'owner': 'root', 'content': b'',
            }
        return len(self.nodes)

    def _read_csv(self, path):
        """Читает CSV-файл и проверяет каждую строку."""
        with open(path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            self._check_header(reader)
            for line_num, row in enumerate(reader, 2):
                self._add_row(row, line_num)

    def _check_header(self, reader):
        """Проверяет наличие обязательных колонок CSV."""
        if reader.fieldnames is None:
            raise VFSError('файл пустой')
        required = {'type', 'path', 'owner', 'content'}
        missing = required - set(reader.fieldnames)
        if missing:
            raise VFSError(
                f'неверный формат, нет колонок: {missing}'
            )

    def _add_row(self, row, line_num):
        """Проверяет строку и добавляет узел в словарь."""
        if row['type'] not in ('dir', 'file'):
            raise VFSError(
                f'строка {line_num}: неизвестный тип '
                f'"{row["type"]}"'
            )
        content = self._decode(row['content'], line_num)
        self.nodes[row['path']] = {
            'type': row['type'],
            'owner': row['owner'],
            'content': content,
        }

    def _decode(self, text, line_num):
        """Декодирует base64-содержимое файла."""
        if not text:
            return b''
        try:
            return base64.b64decode(text)
        except binascii.Error:
            raise VFSError(f'строка {line_num}: кривой base64')

    def save(self, path):
        """Сохраняет состояние в исходном формате CSV."""
        fields = ['type', 'path', 'owner', 'content']
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for node_path in sorted(self.nodes):
                node = self.nodes[node_path]
                writer.writerow(
                    self._row_for(node_path, node)
                )

    def _row_for(self, node_path, node):
        """Собирает строку CSV для узла."""
        content = ''
        if node['type'] == 'file':
            content = base64.b64encode(
                node['content']
            ).decode()
        return {
            'type': node['type'],
            'path': node_path,
            'owner': node['owner'],
            'content': content,
        }


def parent_of(path):
    """Возвращает родительский путь, None для корня."""
    if path == '/':
        return None
    return path.rsplit('/', 1)[0] or '/'


def normalize_path(path, cwd='/'):
    """Разрешает относительный путь против cwd,
    схлопывает . и .."""
    if not path.startswith('/'):
        path = cwd.rstrip('/') + '/' + path
    stack = []
    for part in path.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            if stack:
                stack.pop()
        else:
            stack.append(part)
    return '/' + '/'.join(stack)
