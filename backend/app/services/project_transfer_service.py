# AIMETA P=项目导入导出服务_整项目传输|R=项目导入导出_备份迁移|NR=不含路由|E=ProjectTransferService|X=internal|A=服务类|D=fastapi,sqlalchemy|S=db|RD=./README.ai
from __future__ import annotations

import enum
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.chapter_blueprint import ChapterBlueprint
from ..models.constitution import NovelConstitution
from ..models.faction import (
    Faction,
    FactionMember,
    FactionRelationship,
    FactionRelationshipHistory,
)
from ..models.foreshadowing import (
    Foreshadowing,
    ForeshadowingAnalysis,
    ForeshadowingReminder,
    ForeshadowingResolution,
    ForeshadowingStatusHistory,
)
from ..models.memory_layer import CausalChain, CharacterState, StoryTimeTracker, TimelineEvent
from ..models.novel import BlueprintCharacter, ChapterEvaluation, NovelProject
from ..models.project_memory import ChapterSnapshot, ProjectMemory
from ..models.writer_persona import WriterPersona
from ..schemas.novel import Blueprint
from ..services.novel_service import NovelService

logger = logging.getLogger(__name__)

EXPORT_FORMAT = "arboris-novel-project"
EXPORT_VERSION = 1
EXPORT_BUNDLE_FORMAT = "arboris-novel-bundle"
EXPORT_BUNDLE_VERSION = 1


class ProjectTransferService:
    """项目导入/导出服务（用于整项目迁移/备份）。"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.novel_service = NovelService(session)

    def _serialize_model(
        self,
        instance: Any,
        *,
        exclude: Optional[set[str]] = None,
        rename: Optional[dict[str, str]] = None,
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        mapper = inspect(instance).mapper
        for attr in mapper.column_attrs:
            key = attr.key
            if exclude and key in exclude:
                continue
            value = getattr(instance, key)
            if isinstance(value, datetime):
                value = value.isoformat()
            if isinstance(value, enum.Enum):
                value = value.value
            output_key = rename.get(key, key) if rename else key
            data[output_key] = value
        return data

    def _serialize_list(
        self,
        items: List[Any],
        *,
        exclude: Optional[set[str]] = None,
        rename: Optional[dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        return [self._serialize_model(item, exclude=exclude, rename=rename) for item in items]

    def _maybe_parse_datetime(self, key: str, value: Any) -> Any:
        if isinstance(value, str) and key.endswith("_at"):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value
        return value

    def _safe_int(self, value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    async def export_project(self, project_id: str, user_id: int) -> Dict[str, Any]:
        project = await self.novel_service.ensure_project_owner(project_id, user_id)

        blueprint = self.novel_service._build_blueprint_schema(project)
        conversations = [
            {
                "role": convo.role,
                "content": convo.content,
                "metadata": convo.metadata,
            }
            for convo in sorted(project.conversations, key=lambda c: c.seq)
        ]

        outlines_map = {outline.chapter_number: outline for outline in project.outlines}
        chapters_map = {chapter.chapter_number: chapter for chapter in project.chapters}
        chapter_numbers = sorted(set(outlines_map.keys()) | set(chapters_map.keys()))

        chapters_payload: List[Dict[str, Any]] = []
        for number in chapter_numbers:
            outline = outlines_map.get(number)
            chapter = chapters_map.get(number)

            versions_payload: List[Dict[str, Any]] = []
            selected_index: Optional[int] = None
            evaluations_payload: List[Dict[str, Any]] = []
            version_index_map: Dict[int, int] = {}

            if chapter:
                fallback_time = datetime.min.replace(tzinfo=timezone.utc)
                versions_sorted = sorted(
                    chapter.versions,
                    key=lambda item: item.created_at or fallback_time,
                )
                for idx, version in enumerate(versions_sorted):
                    version_index_map[version.id] = idx
                    versions_payload.append(
                        {
                            "content": version.content,
                            "metadata": version.metadata,
                            "version_label": version.version_label,
                            "provider": version.provider,
                            "created_at": version.created_at.isoformat()
                            if version.created_at
                            else None,
                        }
                    )
                    if chapter.selected_version_id == version.id:
                        selected_index = idx

                evaluations_sorted = sorted(
                    chapter.evaluations,
                    key=lambda item: item.created_at or fallback_time,
                )
                for evaluation in evaluations_sorted:
                    evaluations_payload.append(
                        {
                            "version_index": version_index_map.get(evaluation.version_id),
                            "decision": evaluation.decision,
                            "feedback": evaluation.feedback,
                            "score": evaluation.score,
                            "created_at": evaluation.created_at.isoformat()
                            if evaluation.created_at
                            else None,
                        }
                    )

            chapters_payload.append(
                {
                    "chapter_number": number,
                    "title": outline.title if outline else f"第{number}章",
                    "summary": outline.summary or "" if outline else "",
                    "outline_metadata": outline.metadata if outline else None,
                    "real_summary": chapter.real_summary if chapter else None,
                    "status": chapter.status if chapter else "not_generated",
                    "word_count": chapter.word_count if chapter else 0,
                    "versions": versions_payload,
                    "selected_version_index": selected_index,
                    "evaluations": evaluations_payload,
                }
            )

        project_memory = await self._load_project_memory(project_id)
        character_name_by_id = {c.id: c.name for c in project.characters}

        constitution = await self._load_constitution(project_id)
        writer_personas = await self._load_writer_personas(project_id)
        factions_bundle = await self._load_factions_bundle(project_id, character_name_by_id)
        memory_layer = await self._load_memory_layer(project_id)
        chapter_blueprints = await self._load_chapter_blueprints(project_id)
        foreshadowing_bundle = await self._load_foreshadowing_bundle(project_id)
        chapter_snapshots = await self._load_chapter_snapshots(project_id)

        return {
            "format": EXPORT_FORMAT,
            "version": EXPORT_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "project": {
                "title": project.title,
                "initial_prompt": project.initial_prompt or "",
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            },
            "blueprint": blueprint.model_dump(),
            "conversation_history": conversations,
            "chapters": chapters_payload,
            "project_memory": project_memory,
            "constitution": constitution,
            "writer_personas": writer_personas,
            "factions": factions_bundle,
            "memory_layer": memory_layer,
            "chapter_blueprints": chapter_blueprints,
            "foreshadowing": foreshadowing_bundle,
            "chapter_snapshots": chapter_snapshots,
        }

    async def export_bundle(self, user_id: int) -> Dict[str, Any]:
        result = await self.session.execute(
            select(NovelProject.id).where(NovelProject.user_id == user_id)
        )
        project_ids = [row[0] for row in result.all()]
        projects = [await self.export_project(pid, user_id) for pid in project_ids]
        return {
            "format": EXPORT_BUNDLE_FORMAT,
            "version": EXPORT_BUNDLE_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "projects": projects,
        }

    async def import_bundle(self, user_id: int, payload: Dict[str, Any]) -> List[str]:
        if not isinstance(payload, dict):
            raise ValueError("导入数据格式不正确")

        fmt = payload.get("format")
        if fmt == EXPORT_BUNDLE_FORMAT:
            projects = payload.get("projects") or []
        elif fmt == EXPORT_FORMAT:
            projects = [payload]
        elif isinstance(payload.get("projects"), list):
            projects = payload.get("projects")
        else:
            projects = [payload]

        ids: List[str] = []
        for item in projects:
            if not isinstance(item, dict):
                continue
            ids.append(await self.import_project(user_id, item))
        return ids

    async def _load_constitution(self, project_id: str) -> Optional[Dict[str, Any]]:
        result = await self.session.execute(
            select(NovelConstitution).where(NovelConstitution.project_id == project_id)
        )
        constitution = result.scalars().first()
        if not constitution:
            return None
        return self._serialize_model(constitution)

    async def _load_writer_personas(self, project_id: str) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            select(WriterPersona).where(WriterPersona.project_id == project_id)
        )
        personas = list(result.scalars().all())
        return self._serialize_list(personas)

    async def _load_factions_bundle(
        self, project_id: str, character_name_by_id: Dict[int, str]
    ) -> Dict[str, Any]:
        factions_result = await self.session.execute(
            select(Faction).where(Faction.project_id == project_id)
        )
        relationships_result = await self.session.execute(
            select(FactionRelationship).where(FactionRelationship.project_id == project_id)
        )
        members_result = await self.session.execute(
            select(FactionMember).where(FactionMember.project_id == project_id)
        )

        factions = list(factions_result.scalars().all())
        relationships = list(relationships_result.scalars().all())
        members = list(members_result.scalars().all())
        rel_ids = [rel.id for rel in relationships]
        history: List[FactionRelationshipHistory] = []
        if rel_ids:
            history_result = await self.session.execute(
                select(FactionRelationshipHistory).where(
                    FactionRelationshipHistory.relationship_id.in_(rel_ids)
                )
            )
            history = list(history_result.scalars().all())

        members_payload = []
        for member in members:
            data = self._serialize_model(member)
            data["character_name"] = character_name_by_id.get(member.character_id)
            members_payload.append(data)

        return {
            "factions": self._serialize_list(factions),
            "relationships": self._serialize_list(relationships),
            "members": members_payload,
            "history": self._serialize_list(history),
        }

    async def _load_memory_layer(self, project_id: str) -> Dict[str, Any]:
        states_result = await self.session.execute(
            select(CharacterState).where(CharacterState.project_id == project_id)
        )
        events_result = await self.session.execute(
            select(TimelineEvent).where(TimelineEvent.project_id == project_id)
        )
        chains_result = await self.session.execute(
            select(CausalChain).where(CausalChain.project_id == project_id)
        )
        tracker_result = await self.session.execute(
            select(StoryTimeTracker).where(StoryTimeTracker.project_id == project_id)
        )
        tracker = tracker_result.scalars().first()
        return {
            "character_states": self._serialize_list(list(states_result.scalars().all())),
            "timeline_events": self._serialize_list(list(events_result.scalars().all())),
            "causal_chains": self._serialize_list(list(chains_result.scalars().all())),
            "story_time_tracker": self._serialize_model(tracker) if tracker else None,
        }

    async def _load_chapter_blueprints(self, project_id: str) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            select(ChapterBlueprint).where(ChapterBlueprint.project_id == project_id)
        )
        return self._serialize_list(list(result.scalars().all()))

    async def _load_foreshadowing_bundle(self, project_id: str) -> Dict[str, Any]:
        foreshadowings_result = await self.session.execute(
            select(Foreshadowing).where(Foreshadowing.project_id == project_id)
        )
        foreshadowings = list(foreshadowings_result.scalars().all())
        fs_ids = [fs.id for fs in foreshadowings]

        resolutions: List[ForeshadowingResolution] = []
        if fs_ids:
            resolutions_result = await self.session.execute(
                select(ForeshadowingResolution).where(
                    ForeshadowingResolution.foreshadowing_id.in_(fs_ids)
                )
            )
            resolutions = list(resolutions_result.scalars().all())

        reminders_result = await self.session.execute(
            select(ForeshadowingReminder).where(ForeshadowingReminder.project_id == project_id)
        )
        reminders = list(reminders_result.scalars().all())

        status_history: List[ForeshadowingStatusHistory] = []
        if fs_ids:
            status_result = await self.session.execute(
                select(ForeshadowingStatusHistory).where(
                    ForeshadowingStatusHistory.foreshadowing_id.in_(fs_ids)
                )
            )
            status_history = list(status_result.scalars().all())

        analysis_result = await self.session.execute(
            select(ForeshadowingAnalysis).where(ForeshadowingAnalysis.project_id == project_id)
        )
        analysis = analysis_result.scalars().first()

        return {
            "items": self._serialize_list(foreshadowings),
            "resolutions": self._serialize_list(resolutions),
            "reminders": self._serialize_list(reminders),
            "status_history": self._serialize_list(status_history),
            "analysis": self._serialize_model(analysis) if analysis else None,
        }

    async def _load_chapter_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            select(ChapterSnapshot).where(ChapterSnapshot.project_id == project_id)
        )
        return self._serialize_list(list(result.scalars().all()))

    async def import_project(self, user_id: int, payload: Dict[str, Any]) -> str:
        if not isinstance(payload, dict):
            raise ValueError("导入数据格式不正确")

        data = self._normalize_payload(payload)

        project_meta = data.get("project", {})
        title = project_meta.get("title") or data.get("title") or "导入的项目"
        initial_prompt = (
            project_meta.get("initial_prompt")
            or data.get("initial_prompt")
            or "导入项目"
        )

        project = await self.novel_service.create_project(user_id, title, initial_prompt)

        blueprint_data = data.get("blueprint")
        if blueprint_data:
            await self.novel_service.replace_blueprint(project.id, Blueprint(**blueprint_data))

        conversations = data.get("conversation_history") or data.get("conversations") or []
        for item in conversations:
            role = item.get("role")
            content = item.get("content")
            if not role or content is None:
                continue
            await self.novel_service.append_conversation(
                project.id,
                role,
                content,
                metadata=item.get("metadata"),
            )

        chapters = data.get("chapters") or []
        chapter_id_map: Dict[int, int] = {}
        for chapter_data in chapters:
            chapter_number = chapter_data.get("chapter_number")
            chapter_id = await self._import_chapter(project.id, chapter_data)
            chapter_number_int = self._safe_int(chapter_number)
            if chapter_id and chapter_number_int is not None:
                chapter_id_map[chapter_number_int] = chapter_id

        if data.get("project_memory"):
            await self._restore_project_memory(project.id, data["project_memory"])

        character_name_map = await self._load_character_name_map(project.id)

        if data.get("constitution"):
            await self._restore_constitution(project.id, data["constitution"])

        if data.get("writer_personas"):
            await self._restore_writer_personas(project.id, data["writer_personas"])

        if data.get("factions"):
            await self._restore_factions_bundle(project.id, data["factions"], character_name_map)

        if data.get("memory_layer"):
            await self._restore_memory_layer(project.id, data["memory_layer"], character_name_map)

        foreshadowing_id_map: Dict[int, int] = {}
        if data.get("foreshadowing"):
            foreshadowing_id_map = await self._restore_foreshadowing_bundle(
                project.id, data["foreshadowing"], chapter_id_map
            )

        if data.get("chapter_blueprints"):
            await self._restore_chapter_blueprints(
                project.id, data["chapter_blueprints"], foreshadowing_id_map
            )

        if data.get("chapter_snapshots"):
            await self._restore_chapter_snapshots(project.id, data["chapter_snapshots"])

        if project_meta.get("status"):
            project.status = project_meta.get("status")
            await self.session.commit()

        return project.id

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        fmt = payload.get("format")
        if fmt and fmt != EXPORT_FORMAT:
            raise ValueError("不是支持的项目导入文件")

        if "format" in payload:
            return payload

        # 兼容直接使用 /api/novels/{id} 的返回体
        return {
            "project": {
                "title": payload.get("title"),
                "initial_prompt": payload.get("initial_prompt"),
                "status": payload.get("status"),
            },
            "blueprint": payload.get("blueprint"),
            "conversation_history": payload.get("conversation_history"),
            "chapters": payload.get("chapters"),
        }

    async def _load_character_name_map(self, project_id: str) -> Dict[str, int]:
        result = await self.session.execute(
            select(BlueprintCharacter).where(BlueprintCharacter.project_id == project_id)
        )
        characters = list(result.scalars().all())
        return {c.name: c.id for c in characters if c.name}

    async def _restore_constitution(self, project_id: str, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            return
        result = await self.session.execute(
            select(NovelConstitution).where(NovelConstitution.project_id == project_id)
        )
        constitution = result.scalars().first()
        if not constitution:
            constitution = NovelConstitution(project_id=project_id)
            self.session.add(constitution)

        for key, value in data.items():
            if key in {"id", "project_id", "created_at", "updated_at"}:
                continue
            if hasattr(constitution, key):
                setattr(constitution, key, self._maybe_parse_datetime(key, value))
        await self.session.commit()

    async def _restore_writer_personas(self, project_id: str, data: List[Dict[str, Any]]) -> None:
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            persona = WriterPersona(project_id=project_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at"}:
                    continue
                if hasattr(persona, key):
                    setattr(persona, key, self._maybe_parse_datetime(key, value))
            self.session.add(persona)
        await self.session.commit()

    async def _restore_factions_bundle(
        self,
        project_id: str,
        data: Dict[str, Any],
        character_name_map: Dict[str, int],
    ) -> None:
        if not isinstance(data, dict):
            return

        faction_id_map: Dict[int, int] = {}
        relationship_id_map: Dict[int, int] = {}

        factions = data.get("factions") or []
        for item in factions:
            if not isinstance(item, dict):
                continue
            old_id = item.get("id")
            faction = Faction(project_id=project_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at"}:
                    continue
                if hasattr(faction, key):
                    setattr(faction, key, self._maybe_parse_datetime(key, value))
            self.session.add(faction)
            await self.session.flush()
            old_id_int = self._safe_int(old_id)
            if old_id_int is not None:
                faction_id_map[old_id_int] = faction.id

        relationships = data.get("relationships") or []
        for item in relationships:
            if not isinstance(item, dict):
                continue
            old_id = item.get("id")
            from_id = item.get("faction_from_id")
            to_id = item.get("faction_to_id")
            if from_id is None or to_id is None:
                continue
            from_id_int = self._safe_int(from_id)
            to_id_int = self._safe_int(to_id)
            if from_id_int is None or to_id_int is None:
                continue
            mapped_from = faction_id_map.get(from_id_int)
            mapped_to = faction_id_map.get(to_id_int)
            if not mapped_from or not mapped_to:
                continue
            relationship = FactionRelationship(
                project_id=project_id,
                faction_from_id=mapped_from,
                faction_to_id=mapped_to,
            )
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at", "faction_from_id", "faction_to_id"}:
                    continue
                if hasattr(relationship, key):
                    setattr(relationship, key, self._maybe_parse_datetime(key, value))
            self.session.add(relationship)
            await self.session.flush()
            old_id_int = self._safe_int(old_id)
            if old_id_int is not None:
                relationship_id_map[old_id_int] = relationship.id

        members = data.get("members") or []
        for item in members:
            if not isinstance(item, dict):
                continue
            faction_old_id = item.get("faction_id")
            if faction_old_id is None:
                continue
            faction_old_id_int = self._safe_int(faction_old_id)
            faction_id = faction_id_map.get(faction_old_id_int) if faction_old_id_int is not None else None
            if not faction_id:
                continue
            character_name = item.get("character_name")
            character_id = character_name_map.get(character_name or "")
            if not character_id:
                continue
            member = FactionMember(
                project_id=project_id,
                faction_id=faction_id,
                character_id=character_id,
            )
            for key, value in item.items():
                if key in {
                    "id",
                    "project_id",
                    "created_at",
                    "updated_at",
                    "faction_id",
                    "character_id",
                    "character_name",
                }:
                    continue
                if hasattr(member, key):
                    setattr(member, key, self._maybe_parse_datetime(key, value))
            self.session.add(member)

        history = data.get("history") or []
        for item in history:
            if not isinstance(item, dict):
                continue
            old_rel_id = item.get("relationship_id")
            if old_rel_id is None:
                continue
            old_rel_id_int = self._safe_int(old_rel_id)
            new_rel_id = relationship_id_map.get(old_rel_id_int) if old_rel_id_int is not None else None
            if not new_rel_id:
                continue
            history_item = FactionRelationshipHistory(relationship_id=new_rel_id)
            for key, value in item.items():
                if key in {"id", "created_at", "updated_at", "relationship_id"}:
                    continue
                if hasattr(history_item, key):
                    setattr(history_item, key, self._maybe_parse_datetime(key, value))
            self.session.add(history_item)

        await self.session.commit()

    async def _restore_memory_layer(
        self,
        project_id: str,
        data: Dict[str, Any],
        character_name_map: Dict[str, int],
    ) -> None:
        if not isinstance(data, dict):
            return

        character_states = data.get("character_states") or []
        for item in character_states:
            if not isinstance(item, dict):
                continue
            character_name = item.get("character_name")
            character_id = character_name_map.get(character_name or "")
            if not character_id:
                continue
            state = CharacterState(project_id=project_id, character_id=character_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at", "character_id"}:
                    continue
                if hasattr(state, key):
                    setattr(state, key, self._maybe_parse_datetime(key, value))
            self.session.add(state)

        timeline_events = data.get("timeline_events") or []
        event_id_map: Dict[int, int] = {}
        pending_event_refs: List[tuple[TimelineEvent, Dict[str, Any]]] = []
        for item in timeline_events:
            if not isinstance(item, dict):
                continue
            old_id = item.get("id")
            event = TimelineEvent(project_id=project_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "caused_by_event_id", "leads_to_event_ids"}:
                    continue
                if hasattr(event, key):
                    setattr(event, key, self._maybe_parse_datetime(key, value))
            self.session.add(event)
            await self.session.flush()
            old_id_int = self._safe_int(old_id)
            if old_id_int is not None:
                event_id_map[old_id_int] = event.id
            pending_event_refs.append((event, item))

        for event, item in pending_event_refs:
            caused_by = item.get("caused_by_event_id")
            caused_by_int = self._safe_int(caused_by)
            if caused_by_int is not None and caused_by_int in event_id_map:
                event.caused_by_event_id = event_id_map[caused_by_int]
            leads_to = item.get("leads_to_event_ids")
            if isinstance(leads_to, list):
                mapped_ids: List[Any] = []
                for raw_id in leads_to:
                    raw_id_int = self._safe_int(raw_id)
                    if raw_id_int is not None and raw_id_int in event_id_map:
                        mapped_ids.append(event_id_map[raw_id_int])
                    else:
                        mapped_ids.append(raw_id)
                event.leads_to_event_ids = mapped_ids

        causal_chains = data.get("causal_chains") or []
        for item in causal_chains:
            if not isinstance(item, dict):
                continue
            chain = CausalChain(project_id=project_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at", "cause_event_id", "effect_event_id"}:
                    continue
                if hasattr(chain, key):
                    setattr(chain, key, self._maybe_parse_datetime(key, value))
            cause_event = item.get("cause_event_id")
            effect_event = item.get("effect_event_id")
            cause_event_int = self._safe_int(cause_event)
            effect_event_int = self._safe_int(effect_event)
            if cause_event_int is not None:
                chain.cause_event_id = event_id_map.get(cause_event_int)
            if effect_event_int is not None:
                chain.effect_event_id = event_id_map.get(effect_event_int)
            self.session.add(chain)

        tracker = data.get("story_time_tracker")
        if isinstance(tracker, dict):
            tracker_obj = StoryTimeTracker(project_id=project_id)
            for key, value in tracker.items():
                if key in {"id", "project_id", "created_at", "updated_at"}:
                    continue
                if hasattr(tracker_obj, key):
                    setattr(tracker_obj, key, self._maybe_parse_datetime(key, value))
            self.session.add(tracker_obj)

        await self.session.commit()

    async def _restore_foreshadowing_bundle(
        self,
        project_id: str,
        data: Dict[str, Any],
        chapter_id_map: Dict[int, int],
    ) -> Dict[int, int]:
        if not isinstance(data, dict):
            return {}

        fs_id_map: Dict[int, int] = {}

        items = data.get("items") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            old_id = item.get("id")
            chapter_number = item.get("chapter_number")
            chapter_number_int = self._safe_int(chapter_number)
            if chapter_number_int is None:
                continue
            chapter_id = chapter_id_map.get(chapter_number_int)
            if not chapter_id:
                continue
            fs = Foreshadowing(project_id=project_id, chapter_id=chapter_id, chapter_number=chapter_number_int)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at", "chapter_id", "resolved_chapter_id"}:
                    continue
                if hasattr(fs, key):
                    setattr(fs, key, self._maybe_parse_datetime(key, value))
            resolved_chapter_number = item.get("resolved_chapter_number")
            resolved_chapter_number_int = self._safe_int(resolved_chapter_number)
            if resolved_chapter_number_int is not None:
                fs.resolved_chapter_id = chapter_id_map.get(resolved_chapter_number_int)
            self.session.add(fs)
            await self.session.flush()
            old_id_int = self._safe_int(old_id)
            if old_id_int is not None:
                fs_id_map[old_id_int] = fs.id

        resolutions = data.get("resolutions") or []
        for item in resolutions:
            if not isinstance(item, dict):
                continue
            old_fs_id = item.get("foreshadowing_id")
            old_fs_id_int = self._safe_int(old_fs_id)
            new_fs_id = fs_id_map.get(old_fs_id_int) if old_fs_id_int is not None else None
            if not new_fs_id:
                continue
            chapter_number = item.get("resolved_at_chapter_number")
            chapter_number_int = self._safe_int(chapter_number)
            chapter_id = chapter_id_map.get(chapter_number_int) if chapter_number_int is not None else None
            if not chapter_id:
                continue
            resolution = ForeshadowingResolution(
                foreshadowing_id=new_fs_id,
                resolved_at_chapter_id=chapter_id,
                resolved_at_chapter_number=chapter_number_int or 0,
            )
            for key, value in item.items():
                if key in {
                    "id",
                    "foreshadowing_id",
                    "resolved_at_chapter_id",
                    "created_at",
                    "updated_at",
                }:
                    continue
                if hasattr(resolution, key):
                    setattr(resolution, key, self._maybe_parse_datetime(key, value))
            self.session.add(resolution)

        reminders = data.get("reminders") or []
        for item in reminders:
            if not isinstance(item, dict):
                continue
            old_fs_id = item.get("foreshadowing_id")
            old_fs_id_int = self._safe_int(old_fs_id)
            new_fs_id = fs_id_map.get(old_fs_id_int) if old_fs_id_int is not None else None
            if not new_fs_id:
                continue
            reminder = ForeshadowingReminder(project_id=project_id, foreshadowing_id=new_fs_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at", "foreshadowing_id"}:
                    continue
                if hasattr(reminder, key):
                    setattr(reminder, key, self._maybe_parse_datetime(key, value))
            self.session.add(reminder)

        status_history = data.get("status_history") or []
        for item in status_history:
            if not isinstance(item, dict):
                continue
            old_fs_id = item.get("foreshadowing_id")
            old_fs_id_int = self._safe_int(old_fs_id)
            new_fs_id = fs_id_map.get(old_fs_id_int) if old_fs_id_int is not None else None
            if not new_fs_id:
                continue
            history = ForeshadowingStatusHistory(foreshadowing_id=new_fs_id)
            for key, value in item.items():
                if key in {"id", "created_at", "foreshadowing_id"}:
                    continue
                if hasattr(history, key):
                    setattr(history, key, self._maybe_parse_datetime(key, value))
            self.session.add(history)

        analysis = data.get("analysis")
        if isinstance(analysis, dict):
            analysis_obj = ForeshadowingAnalysis(project_id=project_id)
            for key, value in analysis.items():
                if key in {"id", "project_id", "analyzed_at", "updated_at"}:
                    continue
                if hasattr(analysis_obj, key):
                    setattr(analysis_obj, key, self._maybe_parse_datetime(key, value))
            self.session.add(analysis_obj)

        await self.session.commit()
        return fs_id_map

    async def _restore_chapter_blueprints(
        self,
        project_id: str,
        data: List[Dict[str, Any]],
        foreshadowing_id_map: Dict[int, int],
    ) -> None:
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            blueprint = ChapterBlueprint(project_id=project_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at", "updated_at"}:
                    continue
                if key == "involved_foreshadowings" and isinstance(value, list):
                    mapped = []
                    for raw_id in value:
                        if isinstance(raw_id, int) and raw_id in foreshadowing_id_map:
                            mapped.append(foreshadowing_id_map[raw_id])
                        else:
                            mapped.append(raw_id)
                    setattr(blueprint, key, mapped)
                    continue
                if hasattr(blueprint, key):
                    setattr(blueprint, key, self._maybe_parse_datetime(key, value))
            self.session.add(blueprint)
        await self.session.commit()

    async def _restore_chapter_snapshots(self, project_id: str, data: List[Dict[str, Any]]) -> None:
        if not isinstance(data, list):
            return
        for item in data:
            if not isinstance(item, dict):
                continue
            snapshot = ChapterSnapshot(project_id=project_id)
            for key, value in item.items():
                if key in {"id", "project_id", "created_at"}:
                    continue
                if hasattr(snapshot, key):
                    setattr(snapshot, key, self._maybe_parse_datetime(key, value))
            self.session.add(snapshot)
        await self.session.commit()

    async def _import_chapter(self, project_id: str, chapter_data: Dict[str, Any]) -> Optional[int]:
        chapter_number = chapter_data.get("chapter_number")
        chapter_number_int = self._safe_int(chapter_number)
        if chapter_number_int is None:
            return None

        title = chapter_data.get("title") or f"第{chapter_number_int}章"
        summary = chapter_data.get("summary") or ""
        outline_metadata = chapter_data.get("outline_metadata")

        await self.novel_service.update_or_create_outline(
            project_id,
            chapter_number_int,
            title,
            summary,
            metadata=outline_metadata,
        )

        chapter = await self.novel_service.get_or_create_chapter(project_id, chapter_number_int)

        versions_payload = chapter_data.get("versions")
        contents: List[str] = []
        metadata_list: List[Optional[Dict[str, Any]]] = []

        if isinstance(versions_payload, list) and versions_payload:
            if isinstance(versions_payload[0], str):
                contents = [str(item) for item in versions_payload]
                metadata_list = [None for _ in contents]
            elif isinstance(versions_payload[0], dict):
                for item in versions_payload:
                    contents.append(item.get("content") or "")
                    metadata_list.append(item.get("metadata"))
        else:
            legacy_content = chapter_data.get("content")
            if legacy_content:
                contents = [legacy_content]
                metadata_list = [None]

        selected_index = chapter_data.get("selected_version_index")
        if selected_index is None and contents:
            selected_content = chapter_data.get("content")
            if selected_content in contents:
                selected_index = contents.index(selected_content)

        if contents:
            created_versions = await self.novel_service.replace_chapter_versions(
                chapter,
                contents,
                metadata=metadata_list,
            )

            await self._restore_evaluations(
                chapter.id,
                created_versions,
                chapter_data,
                selected_index,
            )

            if selected_index is not None:
                try:
                    selected_index_int = self._safe_int(selected_index)
                    if selected_index_int is not None:
                        await self.novel_service.select_chapter_version(chapter, selected_index_int)
                except Exception:
                    logger.warning(
                        "导入章节选中版本失败: project=%s chapter=%s index=%s",
                        project_id,
                        chapter_number_int,
                        selected_index,
                )

        if chapter_data.get("real_summary") is not None:
            chapter.real_summary = chapter_data.get("real_summary")
        status_value = chapter_data.get("status") or chapter_data.get("generation_status")
        if status_value is not None:
            chapter.status = status_value
        if chapter_data.get("word_count") is not None:
            chapter.word_count = chapter_data.get("word_count")

        await self.session.commit()
        return chapter.id

    async def _restore_evaluations(
        self,
        chapter_id: int,
        versions: List[Any],
        chapter_data: Dict[str, Any],
        selected_index: Optional[int],
    ) -> None:
        version_id_map = {idx: version.id for idx, version in enumerate(versions)}

        evaluations = chapter_data.get("evaluations")
        if isinstance(evaluations, list) and evaluations:
            for item in evaluations:
                version_index = item.get("version_index")
                version_id = version_id_map.get(version_index) if version_index is not None else None
                self.session.add(
                    ChapterEvaluation(
                        chapter_id=chapter_id,
                        version_id=version_id,
                        decision=item.get("decision"),
                        feedback=item.get("feedback"),
                        score=item.get("score"),
                    )
                )
            await self.session.commit()
            return

        legacy_eval = chapter_data.get("evaluation")
        if legacy_eval:
            version_id = version_id_map.get(selected_index) if selected_index is not None else None
            self.session.add(
                ChapterEvaluation(
                    chapter_id=chapter_id,
                    version_id=version_id,
                    decision="imported",
                    feedback=legacy_eval,
                )
            )
            await self.session.commit()

    async def _load_project_memory(self, project_id: str) -> Optional[Dict[str, Any]]:
        result = await self.session.execute(
            select(ProjectMemory).where(ProjectMemory.project_id == project_id)
        )
        memory = result.scalars().first()
        if not memory:
            return None
        return {
            "global_summary": memory.global_summary,
            "plot_arcs": memory.plot_arcs,
            "story_timeline_summary": memory.story_timeline_summary,
            "last_updated_chapter": memory.last_updated_chapter,
            "version": memory.version,
            "extra": memory.extra,
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
        }

    async def _restore_project_memory(self, project_id: str, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            return

        result = await self.session.execute(
            select(ProjectMemory).where(ProjectMemory.project_id == project_id)
        )
        memory = result.scalars().first()
        if not memory:
            memory = ProjectMemory(project_id=project_id)
            self.session.add(memory)

        memory.global_summary = data.get("global_summary")
        memory.plot_arcs = data.get("plot_arcs")
        memory.story_timeline_summary = data.get("story_timeline_summary")
        memory.last_updated_chapter = data.get("last_updated_chapter") or 0
        memory.version = data.get("version") or 1
        memory.extra = data.get("extra")

        await self.session.commit()
