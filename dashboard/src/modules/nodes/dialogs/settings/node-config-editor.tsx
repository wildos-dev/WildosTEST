import * as React from "react";
import { useNodesSettings } from "./use-nodes-settings";
import { Button, Awaiting, Loading } from "@wildosvpn/common/components";
import { useTranslation } from "react-i18next";
import type { NodeType } from "../..";

const Editor = React.lazy(() => import("@monaco-editor/react"));

export const NodeConfigEditor = ({
  entity,
  backend,
}: { entity: NodeType; backend: string }) => {
  const { t } = useTranslation();
  const {
    payloadValidity,
    language,
    config,
    isFetching,
    handleConfigSave,
    handleConfigChange,
    handleEditorValidation,
  } = useNodesSettings(entity, backend);

  return (
    <>
      <Awaiting
        isFetching={isFetching}
        Component={
          <React.Suspense fallback={<Loading />}>
            <Editor
              height="50vh"
              className="rounded-sm border"
              defaultLanguage={language}
              theme="vs-dark"
              defaultValue={config}
              onChange={handleConfigChange}
              onValidate={handleEditorValidation}
            />
          </React.Suspense>
        }
      />
      <Button
        className="w-full"
        variant={!payloadValidity ? "destructive" : "default"}
        onClick={handleConfigSave}
        disabled={!payloadValidity}
      >
        {t("save")}
      </Button>
    </>
  );
};
