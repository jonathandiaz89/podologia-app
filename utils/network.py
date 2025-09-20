# utils/network.py
import threading
from queue import Queue
from functools import wraps

def timeout(seconds=10):
    """Decorador para timeout en operaciones de red"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_queue = Queue()
            
            def worker():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(('success', result))
                except Exception as e:
                    result_queue.put(('error', e))
            
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                raise TimeoutError(f"La operación excedió el tiempo de {seconds} segundos")
                
            if result_queue.empty():
                raise Exception("La operación no retornó resultados")
                
            status, result = result_queue.get()
            if status == 'error':
                raise result
            return result
        return wrapper
    return decorator