
fn main() {
    let (protoc_bin, _) = protoc_prebuilt::init("22.0").unwrap();
    std::env::set_var("PROTOC", protoc_bin);

    prost_build::compile_protos(
        &["../schemas/swap_event.proto"],
        &["../schemas"],
    )
    .expect("Failed to compile protobufs");
}
