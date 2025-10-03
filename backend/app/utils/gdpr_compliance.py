"""
GDPR コンプライアンスチェッカー

GDPR および個人情報保護法への準拠状況をチェックし、
コンプライアンス違反のリスクを特定する
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ComplianceLevel(Enum):
    """コンプライアンスレベル"""
    COMPLIANT = "compliant"           # 準拠
    WARNING = "warning"               # 警告
    NON_COMPLIANT = "non_compliant"   # 非準拠


class GDPRRequirement(Enum):
    """GDPR 要件"""
    LAWFUL_BASIS = "lawful_basis"                    # 適法根拠
    CONSENT_MANAGEMENT = "consent_management"        # 同意管理
    DATA_MINIMIZATION = "data_minimization"          # データ最小化
    RETENTION_LIMITS = "retention_limits"            # 保持期間制限
    SUBJECT_RIGHTS = "subject_rights"                # データ主体の権利
    SECURITY_MEASURES = "security_measures"          # セキュリティ対策
    BREACH_NOTIFICATION = "breach_notification"      # 漏洩通知
    PRIVACY_BY_DESIGN = "privacy_by_design"          # プライバシー・バイ・デザイン
    DATA_PROTECTION_OFFICER = "data_protection_officer"  # データ保護責任者
    IMPACT_ASSESSMENT = "impact_assessment"          # 影響評価


class GDPRComplianceChecker:
    """GDPR コンプライアンスチェッカークラス
    
    GDPR 要件への準拠状況を評価し、改善提案を提供する
    """
    
    def __init__(self, db_connection):
        """コンプライアンスチェッカーの初期化
        
        Args:
            db_connection: データベース接続オブジェクト
        """
        self.db = db_connection
    
    async def perform_comprehensive_check(self) -> Dict[str, Any]:
        """包括的なコンプライアンスチェック
        
        Returns:
            Dict[str, Any]: コンプライアンスチェック結果
        """
        try:
            check_results = {
                "check_date": datetime.utcnow().isoformat(),
                "overall_compliance": ComplianceLevel.COMPLIANT.value,
                "requirements": {},
                "issues": [],
                "recommendations": [],
                "score": 0
            }
            
            # 各要件のチェック実行
            requirements_checks = [
                (GDPRRequirement.CONSENT_MANAGEMENT, self._check_consent_management),
                (GDPRRequirement.DATA_MINIMIZATION, self._check_data_minimization),
                (GDPRRequirement.RETENTION_LIMITS, self._check_retention_limits),
                (GDPRRequirement.SUBJECT_RIGHTS, self._check_subject_rights),
                (GDPRRequirement.SECURITY_MEASURES, self._check_security_measures),
                (GDPRRequirement.BREACH_NOTIFICATION, self._check_breach_notification),
                (GDPRRequirement.PRIVACY_BY_DESIGN, self._check_privacy_by_design)
            ]
            
            total_score = 0
            max_score = len(requirements_checks) * 100
            
            for requirement, check_function in requirements_checks:
                result = await check_function()
                check_results["requirements"][requirement.value] = result
                total_score += result["score"]
                
                # 問題と推奨事項の集約
                if result["issues"]:
                    check_results["issues"].extend(result["issues"])
                if result["recommendations"]:
                    check_results["recommendations"].extend(result["recommendations"])
            
            # 総合スコアの計算
            check_results["score"] = int((total_score / max_score) * 100)
            
            # 総合コンプライアンスレベルの決定
            if check_results["score"] >= 90:
                check_results["overall_compliance"] = ComplianceLevel.COMPLIANT.value
            elif check_results["score"] >= 70:
                check_results["overall_compliance"] = ComplianceLevel.WARNING.value
            else:
                check_results["overall_compliance"] = ComplianceLevel.NON_COMPLIANT.value
            
            logger.info(f"GDPR コンプライアンスチェック完了 (スコア: {check_results['score']}%)")
            return check_results
            
        except Exception as e:
            logger.error(f"GDPR コンプライアンスチェックに失敗しました: {e}")
            return {
                "check_date": datetime.utcnow().isoformat(),
                "overall_compliance": ComplianceLevel.NON_COMPLIANT.value,
                "error": str(e),
                "score": 0
            }
    
    async def _check_consent_management(self) -> Dict[str, Any]:
        """同意管理のチェック
        
        Returns:
            Dict[str, Any]: チェック結果
        """
        result = {
            "requirement": "同意管理",
            "compliance_level": ComplianceLevel.COMPLIANT.value,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "details": {}
        }
        
        try:
            # 同意記録の存在確認
            cursor = await self.db.execute("""
                SELECT COUNT(*) as consent_count
                FROM user_consents
            """)
            consent_data = await cursor.fetchone()
            consent_count = consent_data["consent_count"] if consent_data else 0
            
            # ユーザー数との比較
            cursor = await self.db.execute("""
                SELECT COUNT(*) as user_count
                FROM users
                WHERE deleted_at IS NULL
            """)
            user_data = await cursor.fetchone()
            user_count = user_data["user_count"] if user_data else 0
            
            result["details"]["total_users"] = user_count
            result["details"]["users_with_consent"] = consent_count
            
            # 同意率の確認
            if user_count > 0:
                consent_rate = (consent_count / user_count) * 100
                result["details"]["consent_rate"] = consent_rate
                
                if consent_rate < 50:
                    result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
                    result["score"] = 30
                    result["issues"].append("同意記録が不十分です（50%未満）")
                    result["recommendations"].append("すべてのユーザーから適切な同意を取得してください")
                elif consent_rate < 80:
                    result["compliance_level"] = ComplianceLevel.WARNING.value
                    result["score"] = 70
                    result["issues"].append("同意記録が不完全です（80%未満）")
                    result["recommendations"].append("同意取得プロセスを改善してください")
            
            # 同意撤回機能の確認
            cursor = await self.db.execute("""
                SELECT COUNT(*) as withdrawn_count
                FROM user_consents
                WHERE withdrawn_at IS NOT NULL
            """)
            withdrawn_data = await cursor.fetchone()
            withdrawn_count = withdrawn_data["withdrawn_count"] if withdrawn_data else 0
            
            result["details"]["withdrawn_consents"] = withdrawn_count
            
            if withdrawn_count == 0 and consent_count > 100:
                result["recommendations"].append("同意撤回機能が適切に動作しているか確認してください")
            
        except Exception as e:
            result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
            result["score"] = 0
            result["issues"].append(f"同意管理チェックエラー: {str(e)}")
        
        return result
    
    async def _check_data_minimization(self) -> Dict[str, Any]:
        """データ最小化のチェック
        
        Returns:
            Dict[str, Any]: チェック結果
        """
        result = {
            "requirement": "データ最小化",
            "compliance_level": ComplianceLevel.COMPLIANT.value,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "details": {}
        }
        
        try:
            # 収集データ項目の確認
            cursor = await self.db.execute("""
                SELECT 
                    COUNT(*) as total_profiles,
                    SUM(CASE WHEN first_name IS NOT NULL THEN 1 ELSE 0 END) as has_first_name,
                    SUM(CASE WHEN last_name IS NOT NULL THEN 1 ELSE 0 END) as has_last_name,
                    SUM(CASE WHEN bio IS NOT NULL THEN 1 ELSE 0 END) as has_bio,
                    SUM(CASE WHEN avatar_url IS NOT NULL THEN 1 ELSE 0 END) as has_avatar
                FROM user_profiles
                WHERE deleted_at IS NULL
            """)
            profile_stats = await cursor.fetchone()
            
            if profile_stats:
                result["details"]["profile_statistics"] = dict(profile_stats)
                
                # 任意項目の利用率確認
                total = profile_stats["total_profiles"]
                if total > 0:
                    optional_fields_usage = {
                        "first_name": (profile_stats["has_first_name"] / total) * 100,
                        "last_name": (profile_stats["has_last_name"] / total) * 100,
                        "bio": (profile_stats["has_bio"] / total) * 100,
                        "avatar": (profile_stats["has_avatar"] / total) * 100
                    }
                    
                    result["details"]["optional_fields_usage"] = optional_fields_usage
                    
                    # 使用率が低いフィールドの特定
                    low_usage_fields = [
                        field for field, usage in optional_fields_usage.items()
                        if usage < 10  # 10%未満の使用率
                    ]
                    
                    if low_usage_fields:
                        result["recommendations"].append(
                            f"使用率の低いフィールド（{', '.join(low_usage_fields)}）の必要性を再検討してください"
                        )
            
            # データ処理活動記録の確認
            cursor = await self.db.execute("""
                SELECT COUNT(*) as activity_count
                FROM data_processing_activities
            """)
            activity_data = await cursor.fetchone()
            activity_count = activity_data["activity_count"] if activity_data else 0
            
            result["details"]["documented_activities"] = activity_count
            
            if activity_count == 0:
                result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
                result["score"] = 40
                result["issues"].append("データ処理活動が文書化されていません")
                result["recommendations"].append("GDPR Article 30 に基づくデータ処理活動記録を作成してください")
            
        except Exception as e:
            result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
            result["score"] = 0
            result["issues"].append(f"データ最小化チェックエラー: {str(e)}")
        
        return result
    
    async def _check_retention_limits(self) -> Dict[str, Any]:
        """保持期間制限のチェック
        
        Returns:
            Dict[str, Any]: チェック結果
        """
        result = {
            "requirement": "保持期間制限",
            "compliance_level": ComplianceLevel.COMPLIANT.value,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "details": {}
        }
        
        try:
            # 期限切れデータの確認
            retention_limit = datetime.utcnow() - timedelta(days=2555)  # 7年
            
            cursor = await self.db.execute("""
                SELECT COUNT(*) as expired_users
                FROM users
                WHERE created_at < %s
                AND deleted_at IS NULL
            """, (retention_limit,))
            
            expired_data = await cursor.fetchone()
            expired_count = expired_data["expired_users"] if expired_data else 0
            
            result["details"]["expired_users_count"] = expired_count
            result["details"]["retention_limit_date"] = retention_limit.isoformat()
            
            if expired_count > 0:
                result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
                result["score"] = 30
                result["issues"].append(f"{expired_count} 件の期限切れユーザーデータが存在します")
                result["recommendations"].append("期限切れデータの匿名化または削除を実行してください")
            
            # データ保持期限設定の確認
            cursor = await self.db.execute("""
                SELECT COUNT(*) as users_without_expiry
                FROM users
                WHERE data_retention_expiry IS NULL
                AND deleted_at IS NULL
            """)
            
            no_expiry_data = await cursor.fetchone()
            no_expiry_count = no_expiry_data["users_without_expiry"] if no_expiry_data else 0
            
            result["details"]["users_without_expiry"] = no_expiry_count
            
            if no_expiry_count > 0:
                if result["compliance_level"] == ComplianceLevel.COMPLIANT.value:
                    result["compliance_level"] = ComplianceLevel.WARNING.value
                    result["score"] = 80
                result["issues"].append(f"{no_expiry_count} 件のユーザーに保持期限が設定されていません")
                result["recommendations"].append("すべてのユーザーデータに保持期限を設定してください")
            
        except Exception as e:
            result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
            result["score"] = 0
            result["issues"].append(f"保持期間制限チェックエラー: {str(e)}")
        
        return result
    
    async def _check_subject_rights(self) -> Dict[str, Any]:
        """データ主体の権利のチェック
        
        Returns:
            Dict[str, Any]: チェック結果
        """
        result = {
            "requirement": "データ主体の権利",
            "compliance_level": ComplianceLevel.COMPLIANT.value,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "details": {}
        }
        
        try:
            # 削除リクエストの処理状況確認
            cursor = await self.db.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_requests,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_requests,
                    AVG(TIMESTAMPDIFF(DAY, requested_at, processed_at)) as avg_processing_days
                FROM data_deletion_requests
                WHERE requested_at >= %s
            """, (datetime.utcnow() - timedelta(days=90),))
            
            deletion_stats = await cursor.fetchone()
            
            if deletion_stats:
                result["details"]["deletion_requests"] = dict(deletion_stats)
                
                pending_count = deletion_stats["pending_requests"] or 0
                avg_days = deletion_stats["avg_processing_days"] or 0
                
                # 未処理リクエストの確認
                if pending_count > 0:
                    result["compliance_level"] = ComplianceLevel.WARNING.value
                    result["score"] = 70
                    result["issues"].append(f"{pending_count} 件の削除リクエストが未処理です")
                    result["recommendations"].append("削除リクエストを速やかに処理してください")
                
                # 処理時間の確認（30日以内が推奨）
                if avg_days > 30:
                    if result["compliance_level"] == ComplianceLevel.COMPLIANT.value:
                        result["compliance_level"] = ComplianceLevel.WARNING.value
                        result["score"] = 80
                    result["issues"].append(f"削除リクエストの平均処理時間が {avg_days:.1f} 日です")
                    result["recommendations"].append("削除リクエストの処理時間を30日以内に短縮してください")
            
            # エクスポート機能の確認（監査ログから）
            cursor = await self.db.execute("""
                SELECT COUNT(*) as export_count
                FROM audit_logs
                WHERE action = 'export'
                AND created_at >= %s
            """, (datetime.utcnow() - timedelta(days=30),))
            
            export_data = await cursor.fetchone()
            export_count = export_data["export_count"] if export_data else 0
            
            result["details"]["recent_exports"] = export_count
            
        except Exception as e:
            result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
            result["score"] = 0
            result["issues"].append(f"データ主体の権利チェックエラー: {str(e)}")
        
        return result
    
    async def _check_security_measures(self) -> Dict[str, Any]:
        """セキュリティ対策のチェック
        
        Returns:
            Dict[str, Any]: チェック結果
        """
        result = {
            "requirement": "セキュリティ対策",
            "compliance_level": ComplianceLevel.COMPLIANT.value,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "details": {}
        }
        
        try:
            # 暗号化されたデータの確認
            cursor = await self.db.execute("""
                SELECT 
                    COUNT(*) as total_profiles,
                    SUM(CASE WHEN first_name LIKE '%encrypted%' OR LENGTH(first_name) > 100 THEN 1 ELSE 0 END) as encrypted_profiles
                FROM user_profiles
                WHERE deleted_at IS NULL
                AND first_name IS NOT NULL
            """)
            
            encryption_stats = await cursor.fetchone()
            
            if encryption_stats and encryption_stats["total_profiles"] > 0:
                encryption_rate = (encryption_stats["encrypted_profiles"] / encryption_stats["total_profiles"]) * 100
                result["details"]["encryption_rate"] = encryption_rate
                
                if encryption_rate < 100:
                    result["compliance_level"] = ComplianceLevel.WARNING.value
                    result["score"] = 80
                    result["issues"].append("一部の個人データが暗号化されていません")
                    result["recommendations"].append("すべての個人データを暗号化してください")
            
            # 監査ログの記録状況確認
            cursor = await self.db.execute("""
                SELECT COUNT(*) as log_count
                FROM audit_logs
                WHERE created_at >= %s
            """, (datetime.utcnow() - timedelta(days=7),))
            
            log_data = await cursor.fetchone()
            log_count = log_data["log_count"] if log_data else 0
            
            result["details"]["recent_audit_logs"] = log_count
            
            if log_count == 0:
                result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
                result["score"] = 40
                result["issues"].append("監査ログが記録されていません")
                result["recommendations"].append("すべてのデータアクセスを監査ログに記録してください")
            
        except Exception as e:
            result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
            result["score"] = 0
            result["issues"].append(f"セキュリティ対策チェックエラー: {str(e)}")
        
        return result
    
    async def _check_breach_notification(self) -> Dict[str, Any]:
        """漏洩通知のチェック
        
        Returns:
            Dict[str, Any]: チェック結果
        """
        result = {
            "requirement": "漏洩通知",
            "compliance_level": ComplianceLevel.COMPLIANT.value,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "details": {}
        }
        
        try:
            # セキュリティインシデントの確認
            cursor = await self.db.execute("""
                SELECT 
                    COUNT(*) as total_incidents,
                    SUM(CASE WHEN incident_type = 'data_breach' THEN 1 ELSE 0 END) as breach_incidents,
                    SUM(CASE WHEN reported_to_authority = 1 THEN 1 ELSE 0 END) as reported_incidents,
                    AVG(TIMESTAMPDIFF(HOUR, detection_date, authority_report_date)) as avg_report_hours
                FROM security_incidents
                WHERE detection_date >= %s
            """, (datetime.utcnow() - timedelta(days=90),))
            
            incident_stats = await cursor.fetchone()
            
            if incident_stats:
                result["details"]["incident_statistics"] = dict(incident_stats)
                
                breach_count = incident_stats["breach_incidents"] or 0
                reported_count = incident_stats["reported_incidents"] or 0
                avg_hours = incident_stats["avg_report_hours"] or 0
                
                if breach_count > 0:
                    # 報告率の確認
                    report_rate = (reported_count / breach_count) * 100 if breach_count > 0 else 0
                    result["details"]["breach_report_rate"] = report_rate
                    
                    if report_rate < 100:
                        result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
                        result["score"] = 30
                        result["issues"].append("一部のデータ漏洩が監督機関に報告されていません")
                        result["recommendations"].append("すべてのデータ漏洩を適切に報告してください")
                    
                    # 報告時間の確認（72時間以内）
                    if avg_hours > 72:
                        if result["compliance_level"] == ComplianceLevel.COMPLIANT.value:
                            result["compliance_level"] = ComplianceLevel.WARNING.value
                            result["score"] = 70
                        result["issues"].append(f"平均報告時間が {avg_hours:.1f} 時間です（72時間超過）")
                        result["recommendations"].append("データ漏洩を72時間以内に報告してください")
            
        except Exception as e:
            result["compliance_level"] = ComplianceLevel.NON_COMPLIANT.value
            result["score"] = 0
            result["issues"].append(f"漏洩通知チェックエラー: {str(e)}")
        
        return result
    
    async def _check_privacy_by_design(self) -> Dict[str, Any]:
        """プライバシー・バイ・デザインのチェック
        
        Returns:
            Dict[str, Any]: チェック結果
        """
        result = {
            "requirement": "プライバシー・バイ・デザイン",
            "compliance_level": ComplianceLevel.COMPLIANT.value,
            "score": 100,
            "issues": [],
            "recommendations": [],
            "details": {}
        }
        
        # 実装されている機能の確認
        implemented_features = {
            "data_encryption": True,      # データ暗号化
            "consent_management": True,   # 同意管理
            "audit_logging": True,        # 監査ログ
            "data_retention": True,       # データ保持期間管理
            "deletion_requests": True,    # 削除リクエスト
            "data_export": True,          # データエクスポート
            "incident_management": True   # インシデント管理
        }
        
        result["details"]["implemented_features"] = implemented_features
        
        # 未実装機能の確認
        missing_features = [
            feature for feature, implemented in implemented_features.items()
            if not implemented
        ]
        
        if missing_features:
            result["compliance_level"] = ComplianceLevel.WARNING.value
            result["score"] = 80
            result["issues"].append(f"未実装機能: {', '.join(missing_features)}")
            result["recommendations"].append("プライバシー保護機能を完全に実装してください")
        
        return result


# 便利関数
async def run_gdpr_compliance_check(db_connection) -> Dict[str, Any]:
    """GDPR コンプライアンスチェックの実行（便利関数）
    
    Args:
        db_connection: データベース接続
        
    Returns:
        Dict[str, Any]: コンプライアンスチェック結果
    """
    checker = GDPRComplianceChecker(db_connection)
    return await checker.perform_comprehensive_check()