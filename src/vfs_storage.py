import csv
import base64
import binascii


class VFSError(Exception):
    """Ошибка загрузки/сохранения VFS."""


class VFSStorage:
    """Виртуальная ФС в памяти. Плоский словарь: полный путь -> узел.
    Вложенность выражается через пути, а не через вложенные словари."""

    def __init__(self):
        self.nodes = {}
        self.cwd = '/'

    def load(self, path):
        """Загружает VFS из CSV. Кидает VFSError при проблемах."""
        self.nodes = {}
        try:
            with open(path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)

                if reader.fieldnames is None:
                    raise VFSError('файл пустой')

                required = {'type', 'path', 'owner', 'content'}
                missing = required - set(reader.fieldnames)
                if missing:
                    raise VFSError(f'неверный формат, нет колонок: {missing}')

                for line_num, row in enumerate(reader, 2):
                    if row['type'] not in ('dir', 'file'):
                        raise VFSError(f'строка {line_num}: неизвестный тип "{row["type"]}"')
                    try:
                        content = base64.b64decode(row['content']) if row['content'] else b''
                    except binascii.Error:
                        raise VFSError(f'строка {line_num}: кривой base64')

                    self.nodes[row['path']] = {
                        'type': row['type'],
                        'owner': row['owner'],
                        'content': content,
                    }
        except FileNotFoundError:
            raise VFSError(f'файл не найден: {path}')
        except csv.Error as e:
            raise VFSError(f'неверный CSV-формат: {e}')

        if not self.nodes:
            raise VFSError('VFS пустая')
        if '/' not in self.nodes:
            self.nodes['/'] = {'type': 'dir', 'owner': 'root', 'content': b''}
        return len(self.nodes)

    def save(self, path):
        """Сохраняет состояние в исходном формате CSV."""
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['type', 'path', 'owner', 'content'])
            writer.writeheader()
            for node_path in sorted(self.nodes):
                node = self.nodes[node_path]
                writer.writerow({
                    'type': node['type'],
                    'path': node_path,
                    'owner': node['owner'],
                    'content': base64.b64encode(node['content']).decode() if node['type'] == 'file' else '',
                })

def parent_of(path):
    """Возвращает родительский путь, None для корня."""
    if path == '/':
        return None
    return path.rsplit('/', 1)[0] or '/'
def normalize_path(path, cwd='/'):
    """Разрешает относительный путь против cwd, схлопывает . и .."""
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