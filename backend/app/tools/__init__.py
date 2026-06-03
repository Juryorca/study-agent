from app.tools.registry import ToolRegistry, tool

# Import tool modules so they self-register with global_registry
import app.tools.answer_eval       # noqa: F401
import app.tools.course_search     # noqa: F401
import app.tools.knowledge_extract # noqa: F401
import app.tools.question_gen      # noqa: F401
import app.tools.review_outline    # noqa: F401
import app.tools.study_plan        # noqa: F401
import app.tools.weakness_diag     # noqa: F401
