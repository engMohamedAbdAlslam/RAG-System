from enum import Enum

class VectorDBEnum(Enum):
    QDRANT = "QDRANT"


class DistanceMethodEnum(str,Enum):
    COSINE = "cosine"
    DOT = "dot"