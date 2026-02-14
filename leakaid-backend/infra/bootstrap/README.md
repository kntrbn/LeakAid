# State 用バケット作成（初回のみ）

```bash
cp terraform.tfvars.example terraform.tfvars   # project_id 等を編集
terraform init
terraform apply
```

完了後、`cd ..` で戻り `terraform init` すればメインの infra で GCS backend が使えます。
