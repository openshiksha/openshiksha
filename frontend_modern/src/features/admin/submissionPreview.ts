import type { Question } from '@/types/index';
import type { PackQuestion } from './useContentSubmissions';

/**
 * Map a pack-payload question onto the app's `Question` shape so the existing
 * `QuestionPreviewPanel` renders it verbatim — no parallel preview code. The
 * pack carries taxonomy as human-readable strings (resolved to FKs only at
 * materialization), so the numeric FK fields are synthetic here; the panel
 * only displays the `*_name` strings. Defaults mirror the importer's
 * (`question_type` "mcq", `difficulty` 2) so the reviewer previews exactly
 * what approval would materialize.
 */
export const packQuestionToPreview = (q: PackQuestion, index: number): Question =>
  ({
    id: index + 1,
    standard: q.standard,
    standard_number: q.standard,
    subject: 0,
    subject_name: q.subject,
    chapter: 0,
    chapter_name: q.chapter,
    question_type: q.question_type ?? 'mcq',
    difficulty: q.difficulty ?? 2,
    stem_text: q.stem_text ?? '',
    tags: (q.tags ?? []).map((name, i) => ({ id: i + 1, name, tag_type: 'concept' })),
    subparts: q.subparts.map((sp) => ({
      id: sp.index + 1,
      index: sp.index,
      subpart_type: sp.subpart_type ?? '',
      tags: [],
      question_text: sp.question_text,
      options: sp.options ?? null,
      image_url: sp.image_url,
      solution_text: sp.solution_text,
      hint_text: sp.hint_text,
      // The panel's widget pill keys off this flag; the actual sandbox render
      // happens separately in the page so the reviewer sees the real thing.
      is_interactive: Boolean(sp.widget_kind),
      widget_kind: sp.widget_kind,
      widget_config: sp.widget_config,
    })),
    is_active: true,
    created_at: '',
  }) as unknown as Question;
