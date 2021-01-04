"""Models and functions used in data hashing."""
from PySide2.QtCore import QByteArray, QCryptographicHash, QFile


def file_checksum(
    file_path: str,
    algorithm: QCryptographicHash.Algorithm = QCryptographicHash.Sha256,
) -> QByteArray:
    """
    Compute a checksum of the contents of a file.

    Args:
        file_path: a path to a file
        algorithm: an algorithm used to compute the hash

    Returns:
        The checksum
    """
    f = QFile(file_path)
    if f.open(QFile.ReadOnly):
        h = QCryptographicHash(algorithm)
        if h.addData(f):
            return h.result()
    return QByteArray()
