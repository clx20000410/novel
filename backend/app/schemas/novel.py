# AIMETA P=小说模式_小说和章节请求响应|R=小说结构_章节结构|NR=不含业务逻辑|E=NovelSchema_ChapterSchema|X=internal|A=Pydantic模式|D=pydantic|S=none|RD=./README.ai
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChoiceOption(BaseModel):
    """前端选择项描述，用于动态 UI 控件。"""

    id: str
    label: str


class UIControl(BaseModel):
    """描述前端应渲染的组件类型与配置。"""

    type: str = Field(..., description="控件类型，如 single_choice/text_input")
    options: Optional[List[ChoiceOption]] = Field(default=None, description="可选项列表")
    placeholder: Optional[str] = Field(default=None, description="输入提示文案")


class ConverseResponse(BaseModel):
    """概念对话接口的统一返回体。"""

    ai_message: str
    ui_control: UIControl
    conversation_state: Dict[str, Any]
    is_complete: bool = False
    ready_for_blueprint: Optional[bool] = None


class ConverseRequest(BaseModel):
    """概念对话接口的请求体。"""

    user_input: Dict[str, Any]
    conversation_state: Dict[str, Any]


class ChapterGenerationStatus(str, Enum):
    NOT_GENERATED = "not_generated"
    GENERATING = "generating"
    EVALUATING = "evaluating"
    SELECTING = "selecting"
    FAILED = "failed"
    EVALUATION_FAILED = "evaluation_failed"
    WAITING_FOR_CONFIRM = "waiting_for_confirm"
    SUCCESSFUL = "successful"


class ChapterOutline(BaseModel):
    chapter_number: int
    title: str
    summary: str = ""  # Default to empty string to handle missing AI responses


class Chapter(ChapterOutline):
    real_summary: Optional[str] = None
    content: Optional[str] = None
    versions: Optional[List[str]] = None
    evaluation: Optional[str] = None
    generation_status: ChapterGenerationStatus = ChapterGenerationStatus.NOT_GENERATED
    word_count: Optional[int] = None


class Relationship(BaseModel):
    character_from: str
    character_to: str
    description: str


class Blueprint(BaseModel):
    title: str
    target_audience: str = ""
    genre: str = ""
    style: str = ""
    tone: str = ""
    one_sentence_summary: str = ""
    full_synopsis: str = ""
    world_setting: Dict[str, Any] = {}
    characters: List[Dict[str, Any]] = []
    relationships: List[Relationship] = []
    chapter_outline: List[ChapterOutline] = []
    
    class Config:
        from_attributes = True


class NovelProject(BaseModel):
    id: str
    user_id: int
    title: str
    initial_prompt: str
    status: str
    conversation_history: List[Dict[str, Any]] = []
    blueprint: Optional[Blueprint] = None
    chapters: List[Chapter] = []

    class Config:
        from_attributes = True


class NovelProjectSummary(BaseModel):
    id: str
    title: str
    genre: str
    status: str
    last_edited: str
    completed_chapters: int
    total_chapters: int


class ActiveInspirationResponse(BaseModel):
    """返回当前用户最新一条可继续的灵感记录（可能为空）。"""

    project: Optional[NovelProjectSummary] = None


class BlueprintGenerationResponse(BaseModel):
    blueprint: Blueprint
    ai_message: str


class ChapterGenerationResponse(BaseModel):
    ai_message: str
    chapter_versions: List[Dict[str, Any]]


class NovelSectionType(str, Enum):
    OVERVIEW = "overview"
    WORLD_SETTING = "world_setting"
    CHARACTERS = "characters"
    RELATIONSHIPS = "relationships"
    CHAPTER_OUTLINE = "chapter_outline"
    CHAPTERS = "chapters"


class NovelSectionResponse(BaseModel):
    section: NovelSectionType
    data: Dict[str, Any]


class GenerateChapterRequest(BaseModel):
    chapter_number: int
    writing_notes: Optional[str] = Field(default=None, description="章节额外写作指令")


class FlowConfig(BaseModel):
    preset: str = Field(default="basic", description="basic|enhanced|ultimate|custom")
    versions: Optional[int] = Field(default=None, description="生成版本数量")
    enable_preview: Optional[bool] = Field(default=None, description="是否启用预演生成")
    enable_optimizer: Optional[bool] = Field(default=None, description="是否启用优化器")
    enable_consistency: Optional[bool] = Field(default=None, description="是否启用一致性检查")
    enable_enrichment: Optional[bool] = Field(default=None, description="是否启用字数扩写")
    async_finalize: Optional[bool] = Field(default=None, description="是否异步定稿")
    enable_rag: Optional[bool] = Field(default=None, description="是否启用 RAG")
    rag_mode: Optional[str] = Field(default=None, description="simple|two_stage")


class AdvancedGenerateRequest(BaseModel):
    project_id: str
    chapter_number: int
    writing_notes: Optional[str] = Field(default=None, description="章节额外写作指令")
    flow_config: FlowConfig = Field(default_factory=FlowConfig)


class AdvancedGenerateVariant(BaseModel):
    index: int
    version_id: int
    content: str
    metadata: Optional[Dict[str, Any]] = None


class AdvancedGenerateResponse(BaseModel):
    project_id: str
    chapter_number: int
    preset: str
    best_version_index: int
    variants: List[AdvancedGenerateVariant]
    review_summaries: Dict[str, Any] = Field(default_factory=dict)
    debug_metadata: Optional[Dict[str, Any]] = None


class FinalizeChapterRequest(BaseModel):
    project_id: str
    selected_version_id: int
    skip_vector_update: Optional[bool] = Field(default=False, description="是否跳过向量库更新")


class FinalizeChapterResponse(BaseModel):
    project_id: str
    chapter_number: int
    selected_version_id: int
    result: Dict[str, Any]


class SelectVersionRequest(BaseModel):
    chapter_number: int
    version_index: int


class EvaluateChapterRequest(BaseModel):
    chapter_number: int


class UpdateChapterOutlineRequest(BaseModel):
    chapter_number: int
    title: str
    summary: str


class DeleteChapterRequest(BaseModel):
    chapter_numbers: List[int]


class GenerateOutlineRequest(BaseModel):
    start_chapter: int
    num_chapters: int


class BlueprintPatch(BaseModel):
    one_sentence_summary: Optional[str] = None
    full_synopsis: Optional[str] = None
    world_setting: Optional[Dict[str, Any]] = None
    characters: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[List[Relationship]] = None
    chapter_outline: Optional[List[ChapterOutline]] = None


class EditChapterRequest(BaseModel):
    chapter_number: int
    content: str
