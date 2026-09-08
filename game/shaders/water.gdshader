shader_type spatial;
render_mode specular_schlick_ggx, cull_back;

uniform vec3 deep_color : source_color = vec3(0.004, 0.012, 0.018);
uniform vec3 shallow_color : source_color = vec3(0.02, 0.05, 0.07);
uniform float wave_scale = 0.15;
uniform float wave_speed = 0.6;

void vertex() {
	float t = TIME * wave_speed;
	VERTEX.y += sin(VERTEX.x * 0.4 + t) * wave_scale
			+ cos(VERTEX.z * 0.35 + t * 1.3) * wave_scale * 0.7;
}

void fragment() {
	float t = TIME * wave_speed;
	vec2 p = VERTEX.xz;
	// procedural rippled normal
	float nx = sin(p.x * 1.2 + t * 2.0) * 0.5 + sin(p.x * 3.7 - t * 1.1) * 0.25;
	float nz = cos(p.y * 1.1 + t * 1.7) * 0.5 + cos(p.y * 4.1 + t * 0.9) * 0.25;
	vec3 n = normalize(vec3(nx * 0.25, 1.0, nz * 0.25));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);

	float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	ALBEDO = mix(deep_color, shallow_color, fresnel);
	ROUGHNESS = 0.06;
	SPECULAR = 0.6;
	METALLIC = 0.0;
}
