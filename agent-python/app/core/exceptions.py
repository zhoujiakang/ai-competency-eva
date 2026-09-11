class AgentNotConfigured(RuntimeError):
    """Raised when the model provider is not configured."""


class ModelReplyError(RuntimeError):
    """模型返回的内容无法使用（空回复、JSON 解析失败等）。"""
