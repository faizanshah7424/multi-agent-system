import os
import shutil
import unittest
from core.knowledge.engine import InMemoryGraphEngine
from core.product_builder.business_analyzer import BusinessAnalyzer
from core.product_builder.requirements_engine import RequirementsEngine
from core.product_builder.domain_modeler import DomainModeler
from core.product_builder.database_designer import DatabaseDesigner
from core.product_builder.api_designer import ApiDesigner
from core.product_builder.frontend_architect import FrontendArchitect
from core.product_builder.ui_planner import UIPlanner
from core.product_builder.backend_architect import BackendArchitect
from core.product_builder.testing_planner import TestingPlanner
from core.product_builder.deployment_planner import DeploymentPlanner
from core.product_builder.documentation_generator import DocumentationGenerator
from core.product_builder.product_memory import ProductMemory, ProductRecord
from core.product_builder.product_engine import AutonomousProductBuilder

class TestProductBuilder(unittest.TestCase):
    def setUp(self):
        self.graph = InMemoryGraphEngine()
        self.builder = AutonomousProductBuilder(self.graph)
        self.test_docs_dir = "docs/test_product_specs"
        self.doc_gen = DocumentationGenerator(self.test_docs_dir)

    def tearDown(self):
        if os.path.exists(self.test_docs_dir):
            try:
                shutil.rmtree(self.test_docs_dir)
            except Exception:
                pass
        # Clean test memory db
        test_mem_db = "data/test_prod_memory.db"
        if os.path.exists(test_mem_db):
            try:
                os.remove(test_mem_db)
            except Exception:
                pass

    def test_business_analyzer(self):
        analyzer = BusinessAnalyzer()
        res = analyzer.analyze_business_idea("Hospital Management System")
        self.assertEqual(res.domain, "Healthcare / Medical Operations")
        self.assertIn("Patients", res.stakeholders)
        self.assertIn("Patient", res.entities)

        res_custom = analyzer.analyze_business_idea("Smart Agriculture")
        self.assertEqual(res_custom.domain, "Custom Domain: Smart Agriculture")
        self.assertIn("UserRecord", res_custom.entities)

    def test_requirements_engine(self):
        analyzer = BusinessAnalyzer()
        specs = analyzer.analyze_business_idea("Restaurant POS")
        engine = RequirementsEngine()
        reqs = engine.generate_requirements(specs)
        self.assertIn("Point of Sale", reqs.vision)
        self.assertGreater(len(reqs.functional_reqs), 0)

    def test_domain_modeler_and_designer(self):
        analyzer = BusinessAnalyzer()
        specs = analyzer.analyze_business_idea("Hospital Management System")
        modeler = DomainModeler()
        domain = modeler.model_domain(specs)
        self.assertIn("Patient", domain.entities)
        self.assertEqual(domain.db_tables[0], "tbl_patients")

        designer = DatabaseDesigner()
        db_design = designer.design_database(domain)
        self.assertGreater(len(db_design.ddl_scripts), 0)
        self.assertIn("CREATE TABLE tbl_patients", db_design.ddl_scripts[0])

    def test_api_and_ui_planners(self):
        analyzer = BusinessAnalyzer()
        specs = analyzer.analyze_business_idea("Hospital Management System")
        modeler = DomainModeler()
        domain = modeler.model_domain(specs)

        api_designer = ApiDesigner()
        apis = api_designer.design_apis(domain)
        self.assertGreater(len(apis.endpoints), 0)
        self.assertEqual(apis.endpoints[0].path, "/auth/login")

        fe_arch = FrontendArchitect()
        fe_plan = fe_arch.architect_frontend(domain)
        self.assertIn("PatientView", fe_plan.pages)

        ui_planner = UIPlanner()
        ui_plan = ui_planner.plan_ui(domain)
        self.assertEqual(ui_plan.components[0].name, "PatientForm")

    def test_backend_testing_and_deployment_planners(self):
        analyzer = BusinessAnalyzer()
        specs = analyzer.analyze_business_idea("Hospital Management System")
        modeler = DomainModeler()
        domain = modeler.model_domain(specs)

        be_arch = BackendArchitect()
        be_plan = be_arch.architect_backend(domain)
        self.assertIn("PatientService", be_plan.services)

        t_planner = TestingPlanner()
        t_plan = t_planner.plan_tests(domain)
        self.assertIn("test_patient_crud", t_plan.unit_tests)

        d_planner = DeploymentPlanner()
        d_plan = d_planner.plan_deployment()
        self.assertIn("production", d_plan.environments)

    def test_documentation_generation(self):
        analyzer = BusinessAnalyzer()
        specs = analyzer.analyze_business_idea("Hospital Management System")
        modeler = DomainModeler()
        domain = modeler.model_domain(specs)
        designer = DatabaseDesigner()
        db_design = designer.design_database(domain)
        api_designer = ApiDesigner()
        apis = api_designer.design_apis(domain)
        fe_arch = FrontendArchitect()
        fe_plan = fe_arch.architect_frontend(domain)
        be_arch = BackendArchitect()
        be_plan = be_arch.architect_backend(domain)
        t_planner = TestingPlanner()
        t_plan = t_planner.plan_tests(domain)
        d_planner = DeploymentPlanner()
        d_plan = d_planner.plan_deployment()

        doc_data = {
            "idea": "Hospital Management System",
            "specs": specs.model_dump(),
            "reqs": {"vision": "Hospital Vision", "functional_reqs": ["req1"]},
            "db_design": db_design.model_dump(),
            "api_design": apis.model_dump(),
            "frontend_plan": fe_plan.model_dump(),
            "backend_plan": be_plan.model_dump(),
            "testing_plan": t_plan.model_dump(),
            "deployment_plan": d_plan.model_dump()
        }

        docs_paths = self.doc_gen.generate_documentation(doc_data)
        self.assertEqual(len(docs_paths), 10)
        self.assertTrue(os.path.exists(docs_paths["product_requirements"]))
        self.assertTrue(os.path.exists(docs_paths["executive_summary"]))

    def test_product_memory(self):
        test_mem_db = "data/test_prod_memory.db"
        memory = ProductMemory(test_mem_db)
        record = ProductRecord(
            id="prod_1",
            idea="Hospital Management System",
            domain="Healthcare",
            requirements={"vision": "Hospital Vision"},
            architecture={"db_tables": ["tbl_patients"]},
            generated_documents={"summary": "docs/summary.md"},
            confidence=0.98,
            debate_results={"consensus": "HEX"},
            execution_duration_seconds=1.45
        )
        memory.add_record(record)
        records = memory.list_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].idea, "Hospital Management System")

    def test_full_pipeline_orchestration(self):
        res = self.builder.build_product("Hospital Management System")
        self.assertTrue(res["success"])
        self.assertEqual(res["business_specs"]["domain"], "Healthcare / Medical Operations")
        self.assertEqual(len(res["documents"]), 10)
        self.assertIn("entity_patient", self.graph.nodes)
